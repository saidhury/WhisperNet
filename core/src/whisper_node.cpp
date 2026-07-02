#include "whisper_node.hpp"
#include <iostream>
#include <cstring>
#include <thread>
#include <string>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <BaseTsd.h>
    typedef SSIZE_T ssize_t;
    typedef SOCKET socket_t;
    #define CLOSESOCKET(s) closesocket(s)
    #define SETSOCKOPT_CAST (const char*)
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    typedef int socket_t;
    #define CLOSESOCKET(s) close(s)
    #define SETSOCKOPT_CAST
#endif

#define BUFFER_SIZE 1024

void initialize_networking() {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed." << std::endl;
        exit(1);
    }
#endif
}

#include <atomic>
#include <mutex>

static void (*g_on_message_received)(const char* message, const char* sender_ip, int sender_port) = nullptr;
static socket_t g_sockfd = -1;
static std::atomic<bool> g_running{false};
static std::mutex g_callback_mutex;
static std::thread g_listen_thread;

struct ListenerCleanup {
    ~ListenerCleanup() {
        g_running = false;
        if (g_listen_thread.joinable()) {
            g_listen_thread.join();
        }
        if (g_sockfd != -1) {
#ifdef _WIN32
            closesocket(g_sockfd);
#else
            close(g_sockfd);
#endif
            g_sockfd = -1;
        }
    }
} g_cleanup;

void listen_thread_func(socket_t sockfd) {
    char buffer[BUFFER_SIZE];
    struct sockaddr_in cliaddr;
#ifdef _WIN32
    int len = sizeof(cliaddr);
#else
    socklen_t len = sizeof(cliaddr);
#endif

    while (g_running) {
        fd_set readfds;
        FD_ZERO(&readfds);
        FD_SET(sockfd, &readfds);
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 200000; // 200ms

        int ready = select((int)sockfd + 1, &readfds, nullptr, nullptr, &tv);
        if (!g_running) break;          // check again right after waking up
        if (ready <= 0) continue;       // timeout or interrupted signal, loop again

        ssize_t n = recvfrom(sockfd, buffer, BUFFER_SIZE - 1, 0, (struct sockaddr *)&cliaddr, &len);
        if (n > 0 && g_running) {
            buffer[n] = '\0';
            char sender_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &cliaddr.sin_addr, sender_ip, INET_ADDRSTRLEN);

            std::lock_guard<std::mutex> lock(g_callback_mutex);
            if (g_on_message_received) {
                int sender_port = ntohs(cliaddr.sin_port);
                g_on_message_received(buffer, sender_ip, sender_port);
            }
        } else if (n < 0 || !g_running) {
            break;
        }
    }
}

void send_udp_message_internal(const char* message, const char* recipient_ip, int port, bool is_broadcast) {
    socket_t sockfd;
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("send_udp: socket creation failed");
        return;
    }

    if (is_broadcast) {
        int broadcast_enable = 1;
        if (setsockopt(sockfd, SOL_SOCKET, SO_BROADCAST,
                       SETSOCKOPT_CAST &broadcast_enable, sizeof(broadcast_enable)) < 0) {
            perror("send_udp: setsockopt(SO_BROADCAST) failed");
            CLOSESOCKET(sockfd);
            return;
        }
    }

    struct sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(port);
    if (inet_pton(AF_INET, recipient_ip, &servaddr.sin_addr) != 1) {
        std::cerr << "send_udp: invalid recipient IP: " << recipient_ip << std::endl;
        CLOSESOCKET(sockfd);
        return;
    }

    ssize_t bytes_sent = sendto(sockfd, message, (int)strlen(message), 0,
                                (const struct sockaddr *)&servaddr, sizeof(servaddr));
    if (bytes_sent < 0) {
        perror("send_udp: sendto failed");
    }

    CLOSESOCKET(sockfd);
}

extern "C" {
    int start_udp_listener(int port, void (*on_message_received)(const char* message, const char* sender_ip, int sender_port)) {
        if (g_running) {
            std::cerr << "listen: a listener is already running; call stop_udp_listener() first" << std::endl;
            return -1;
        }

        initialize_networking();
        {
            std::lock_guard<std::mutex> lock(g_callback_mutex);
            g_on_message_received = on_message_received;
        }

        socket_t sockfd;
        if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
            perror("listen: socket creation failed");
            return -1;
        }

        // Apply reuse rules so multiple local instances can grab the broadcast
//         int reuse = 1;
//         setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, SETSOCKOPT_CAST &reuse, sizeof(reuse));
// #ifdef SO_REUSEPORT
//         setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, SETSOCKOPT_CAST &reuse, sizeof(reuse));
// #endif

        struct sockaddr_in servaddr;
        memset(&servaddr, 0, sizeof(servaddr));
        servaddr.sin_family = AF_INET;
        servaddr.sin_addr.s_addr = INADDR_ANY;
        servaddr.sin_port = htons(port);

        if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
            servaddr.sin_port = htons(0);
            if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
                perror("listen: fallback bind failed");
                CLOSESOCKET(sockfd);
                return -1;
            }
        }

        struct sockaddr_in bound_addr;
#ifdef _WIN32
        int addr_len = sizeof(bound_addr);
#else
        socklen_t addr_len = sizeof(bound_addr);
#endif
        int bound_port = port;
        if (getsockname(sockfd, (struct sockaddr *)&bound_addr, &addr_len) == 0) {
            bound_port = ntohs(bound_addr.sin_port);
        }

        g_sockfd = sockfd;
        g_running = true;
        g_listen_thread = std::thread(listen_thread_func, sockfd);
        return bound_port;
    }

    void stop_udp_listener() {
        if (!g_running) return;
        g_running = false;

        if (g_listen_thread.joinable()) {
            g_listen_thread.join();
        }

        if (g_sockfd != -1) {
            CLOSESOCKET(g_sockfd);
            g_sockfd = -1;
        }
    }

    void send_udp_message(const char* message, const char* recipient_ip, int port) {
        initialize_networking();
        std::string ip_str(recipient_ip);
        bool is_broadcast = ip_str.length() > 4 && ip_str.substr(ip_str.length() - 4) == ".255";
        send_udp_message_internal(message, recipient_ip, port, is_broadcast);
    }

    void send_broadcast_message(const char* message, int port) {
        initialize_networking();
        send_udp_message_internal(message, "255.255.255.255", port, true);
    }

    int join_multicast_group(const char* multicast_ip) {
        if (g_sockfd == -1) {
            std::cerr << "Cannot join multicast: listener not started." << std::endl;
            return 0;
        }

        struct ip_mreq mreq;
        if (inet_pton(AF_INET, multicast_ip, &mreq.imr_multiaddr.s_addr) != 1) {
            return 0; // Invalid IP
        }
        mreq.imr_interface.s_addr = htonl(INADDR_ANY);

        if (setsockopt(g_sockfd, IPPROTO_IP, IP_ADD_MEMBERSHIP, SETSOCKOPT_CAST &mreq, sizeof(mreq)) < 0) {
            perror("join_multicast: setsockopt failed");
            return 0;
        }
        return 1;
    }

    int get_local_ip(char* out_buffer, int max_len) {
        initialize_networking();
        
        socket_t sock = socket(AF_INET, SOCK_DGRAM, 0);
        if (sock < 0) return 0;

        struct sockaddr_in serv;
        memset(&serv, 0, sizeof(serv));
        serv.sin_family = AF_INET;
        inet_pton(AF_INET, "8.8.8.8", &serv.sin_addr);
        serv.sin_port = htons(53);

        int result = 0;
        if (connect(sock, (const struct sockaddr*)&serv, sizeof(serv)) == 0) {
            struct sockaddr_in name;
#ifdef _WIN32
            int namelen = sizeof(name);
#else
            socklen_t namelen = sizeof(name);
#endif
            if (getsockname(sock, (struct sockaddr*)&name, &namelen) == 0) {
                inet_ntop(AF_INET, &name.sin_addr, out_buffer, max_len);
                result = 1;
            }
        }
        
        CLOSESOCKET(sock);
        return result;
    }
}