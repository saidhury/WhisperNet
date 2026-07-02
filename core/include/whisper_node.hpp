#ifndef WHISPER_NODE_HPP
#define WHISPER_NODE_HPP

#ifdef _WIN32
    #ifdef BUILDING_DLL
        #define DLL_EXPORT __declspec(dllexport)
    #else
        #define DLL_EXPORT __declspec(dllimport)
    #endif
#else
    #define DLL_EXPORT
#endif

extern "C" {
    DLL_EXPORT int start_udp_listener(int port, void (*on_message_received)(const char* message, const char* sender_ip, int sender_port));
    DLL_EXPORT void stop_udp_listener();
    DLL_EXPORT void send_udp_message(const char* message, const char* recipient_ip, int port);
    DLL_EXPORT void send_broadcast_message(const char* message, int port);
    DLL_EXPORT int join_multicast_group(const char* multicast_ip);
    DLL_EXPORT int get_local_ip(char* out_buffer, int max_len);
}

#endif
