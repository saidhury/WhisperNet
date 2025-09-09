#include "whisper_node.hpp"
#include <iostream>

extern "C" {
    void start_udp_listener(int port, void (*on_message_received)(const char* message, const char* sender_ip)) {
        std::cout << "C++: Listener started on port " << port << std::endl;
    }

    void send_udp_message(const char* message, const char* recipient_ip, int port) {
        std::cout << "C++: Sending '" << message << "' to " << recipient_ip << ":" << port << std::endl;
    }
}
