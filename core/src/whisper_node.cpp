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

static void (*g_on_message_received)(const char* message, const char* sender_ip) = nullptr;

void listen_thread_func(int port) {
    socket_t sockfd;
    struct sockaddr_in servaddr, cliaddr;

    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("listen: socket creation failed");
        return;
    }

    memset(&servaddr, 0, sizeof(servaddr));
    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(port);

    if (bind(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("listen: bind failed");
        CLOSESOCKET(sockfd);
        return;
    }

    char buffer[BUFFER_SIZE];
#ifdef _WIN32
    int len = sizeof(cliaddr);
#else
    socklen_t len = sizeof(cliaddr);
#endif

    while (true) {
        ssize_t n = recvfrom(sockfd, buffer, BUFFER_SIZE - 1, 0, (struct sockaddr *)&cliaddr, &len);
        if (n > 0) {
            buffer[n] = '\0';
            char sender_ip[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &cliaddr.sin_addr, sender_ip, INET_ADDRSTRLEN);
            if (g_on_message_received) {
                g_on_message_received(buffer, sender_ip);
            }
        }
    }

    CLOSESOCKET(sockfd);
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
    inet_pton(AF_INET, recipient_ip, &servaddr.sin_addr);

    ssize_t bytes_sent = sendto(sockfd, message, (int)strlen(message), 0,
                                (const struct sockaddr *)&servaddr, sizeof(servaddr));
    if (bytes_sent < 0) {
        perror("send_udp: sendto failed");
    }

    CLOSESOCKET(sockfd);
}

extern "C" {
    void start_udp_listener(int port, void (*on_message_received)(const char* message, const char* sender_ip)) {
        initialize_networking();
        g_on_message_received = on_message_received;
        std::thread(listen_thread_func, port).detach();
    }

    void send_udp_message(const char* message, const char* recipient_ip, int port) {
        initialize_networking();
        std::string ip_str(recipient_ip);
        bool is_broadcast = ip_str.length() > 4 && ip_str.substr(ip_str.length() - 4) == ".255";
        send_udp_message_internal(message, recipient_ip, port, is_broadcast);
    }
}
