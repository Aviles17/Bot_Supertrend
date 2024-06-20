/*
##################################################################################################################
El siguiente codigo es un servidor de heartbeat que tiene como proposito fundamental la detección de fallos en el
en ejecución del bot. Es decir, si el bot no responde este detectara el fallo.

Para ejecutar el servidor, basta con ejecutar el siguientes comandos:
    g++ Heartbeat_server.cpp -o Heartbeat_server
    ./Heartbeat_server

El servidor esta configurado para comunicarse a traves de una conexión TCP local por el puerto
65432 -> (127.0.0.1:65432)

El codigo tiene un timeout de 60 segundos, por lo que si el bot no responde en este tiempo diagnosticara
el fallo.

Este codigo no esta relacionado al proyecto de forma intrinseca, significando que esta es una pieza totalmente
independiente, que debe ser compilada y ejecutada por separado en otro ambiente.
    Por ende, se recominda copiar el archivo a otro espacio de trabajo una vez clonado el repo
##################################################################################################################
*/

#include <iostream>
#include <string>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <chrono>
#include <thread>

using namespace std;

const int PORT = 65432;
const int TIMEOUT = 120; // Timeout in seconds

int main() {
    //Crear un socket para la comunicación
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        cerr << "Error al crear el socket" << endl;
        return 1;
    }

    //Configurar la dirección del servidor
    sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = inet_addr("127.0.0.1");
    address.sin_port = htons(PORT);

    //Conectar al servidor
    if(bind(sock, (sockaddr *)&address, sizeof(address)) == -1) 
    {
        cerr << "Error al conectar al servidor" << endl;
        return 1;
    }

    //Escuchar por conexiones entrantes
    if(listen(sock, 1) == -1) {
        cerr << "Error al escuchar" << endl;
        return 1;
    }
    cout << "Escuchando en el puerto " << PORT << "..." << endl;

    //Aceptar una nueva conexión
    sockaddr_in client_address;
    socklen_t client_address_size = sizeof(client_address);
    int client_sock = accept(sock, (sockaddr *)&client_address, &client_address_size);
    if (client_sock == -1) {
        cerr << "Error al aceptar la nueva conexión" << endl;
        return 1;
    }
    cout << "Conexión aceptada desde " << inet_ntoa(client_address.sin_addr) << ":" << ntohs(client_address.sin_port) << endl;

    //Crear bucle que escuha por datos entrantes
    char buffer[1024];
    ssize_t bytes_received;
    while (true)
    {
        auto start = chrono::steady_clock::now();
        auto timeout = chrono::seconds(TIMEOUT);
        bool message_received = false;
        bool timeout_exceeded = false; // Flag para controlar la implementación futura en bash

        while (!message_received){
            auto now = chrono::steady_clock::now();
            auto elapsed = now - start;

            if (elapsed >= timeout) {
                timeout_exceeded = true;
                cout << "Timeout excedido sin respuesta" << endl;
                break;
            }

            bytes_received = recv(client_sock, buffer, (sizeof(buffer)-1), 0);

            if (bytes_received > 0) {
                buffer[bytes_received] = '\0';
                cout << "Recibido: " << buffer << endl;
                cout << "Processo en Python activo" << endl;
                message_received = true;
            }
            else {
                //En el caso de no recibir nada se espera 
                this_thread::sleep_for(chrono::milliseconds(100));
            }
        }
    }

    //Cerramos los sockets
    close(client_sock);
    close(sock);
    return 0;

}
