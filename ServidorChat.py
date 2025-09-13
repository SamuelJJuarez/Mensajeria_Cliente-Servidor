import socket
import threading
import time
from datetime import datetime

class ServidorChat:
    def __init__(self, host='localhost', puerto=12345):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = None
        self.clientes = {}  #{nombre: {'socket': socket_obj, 'ip': direccion, 'conectado': True}}
        self.ejecutando = True
        
        # NUEVO: Historial de mensajes del chat general
        self.historial_general = []  # Lista de mensajes del chat general
        self.max_historial = 50  # Máximo de mensajes a mantener
        
    def iniciar_servidor(self):
        """Inicia el servidor con protocolo personalizado"""
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.puerto))
            self.socket_servidor.listen(10)
            
            print(f"🚀 Servidor de chat iniciado en {self.host}:{self.puerto}")
            print("📡 Protocolo personalizado activado")
            print("📜 Historial de chat general habilitado")
            print("💡 Presiona Ctrl+C para detener")
            
            while self.ejecutando:
                try:
                    cliente_socket, direccion = self.socket_servidor.accept()
                    print(f"🔌 Nueva conexión desde {direccion}")
                    
                    # Crear hilo para manejar este cliente
                    hilo_cliente = threading.Thread(
                        target=self.manejar_cliente,
                        args=(cliente_socket, direccion)
                    )
                    hilo_cliente.daemon = True
                    hilo_cliente.start()
                    
                except Exception as e:
                    if self.ejecutando:
                        print(f"❌ Error aceptando conexión: {e}")
                        
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo servidor...")
        except Exception as e:
            print(f"❌ Error iniciando servidor: {e}")
        finally:
            self.detener_servidor()
    
    def manejar_cliente(self, cliente_socket, direccion):
        """Maneja la comunicación con un cliente usando nuestro protocolo"""
        nombre_cliente = None
        
        try:
            while self.ejecutando:
                try:
                    # Recibir mensaje del cliente
                    data = cliente_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    # Procesar mensaje según nuestro protocolo
                    respuesta = self.procesar_mensaje_protocolo(data, cliente_socket, direccion, nombre_cliente)
                    
                    # Si el cliente se registró, actualizar su nombre
                    if respuesta and 'nombre_registrado' in respuesta:
                        nombre_cliente = respuesta['nombre_registrado']
                    
                except socket.error:
                    break
                    
        except Exception as e:
            print(f"❌ Error manejando cliente {direccion}: {e}")
        finally:
            # Limpiar cliente al desconectarse
            if nombre_cliente and nombre_cliente in self.clientes:
                del self.clientes[nombre_cliente]
                print(f"👋 {nombre_cliente} se desconectó")
                
                # NUEVO: Notificar salida del usuario
                self.notificar_usuario_salio(nombre_cliente)
                # Notificar a todos sobre la desconexión
                self.notificar_cambio_usuarios()
            
            cliente_socket.close()
    
    def procesar_mensaje_protocolo(self, mensaje, cliente_socket, direccion, nombre_actual):
        """Procesa mensajes según nuestro protocolo personalizado"""
        try:
            # Nuestro protocolo usa formato: COMANDO|PARAMETROS
            partes = mensaje.split('|', 1)
            comando = partes[0]
            parametros = partes[1] if len(partes) > 1 else ""
            
            if comando == "CONNECT":
                return self.manejar_conexion(parametros, cliente_socket, direccion)
            
            elif comando == "MESSAGE":
                return self.manejar_mensaje_privado(parametros, nombre_actual)
            
            elif comando == "BROADCAST":
                return self.manejar_mensaje_general(parametros, nombre_actual)
            
            elif comando == "GET_USERS":
                return self.enviar_lista_usuarios(cliente_socket)
            
            # NUEVO: Comando para obtener historial
            elif comando == "GET_HISTORY":
                return self.enviar_historial_general(cliente_socket)
            
            elif comando == "PING":
                cliente_socket.send("PONG".encode('utf-8'))
                return None
            
            else:
                cliente_socket.send("ERROR|Comando no reconocido".encode('utf-8'))
                return None
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            cliente_socket.send("ERROR|Error procesando mensaje".encode('utf-8'))
            return None
    
    def manejar_conexion(self, nombre, cliente_socket, direccion):
        """Maneja el registro de un nuevo cliente"""
        if not nombre.strip():
            cliente_socket.send("ERROR|Nombre vacío".encode('utf-8'))
            return None
        
        if nombre in self.clientes:
            cliente_socket.send("ERROR|Nombre ya existe".encode('utf-8'))
            return None
        
        # Registrar cliente
        self.clientes[nombre] = {
            'socket': cliente_socket,
            'ip': direccion[0],
            'puerto': direccion[1],
            'conectado': True
        }
        
        print(f"✅ {nombre} registrado desde {direccion}")
        cliente_socket.send("SUCCESS|Conectado exitosamente".encode('utf-8'))
        
        # NUEVO: Notificar entrada del usuario a todos los demás
        self.notificar_usuario_entro(nombre)
        
        # Notificar a todos los clientes sobre el nuevo usuario
        self.notificar_cambio_usuarios()
        
        return {'nombre_registrado': nombre}
    
    def manejar_mensaje_privado(self, parametros, remitente):
        """Maneja mensajes privados entre usuarios"""
        if not remitente or remitente not in self.clientes:
            return None
        
        try:
            # Formato: DESTINATARIO|MENSAJE
            partes = parametros.split('|', 1)
            destinatario = partes[0]
            mensaje = partes[1] if len(partes) > 1 else ""
            
            if destinatario in self.clientes and self.clientes[destinatario]['conectado']:
                # Enviar mensaje al destinatario
                mensaje_formateado = f"PRIVATE_MSG|{remitente}|{mensaje}"
                self.clientes[destinatario]['socket'].send(mensaje_formateado.encode('utf-8'))
                
                # Confirmar envío al remitente
                self.clientes[remitente]['socket'].send("SUCCESS|Mensaje enviado".encode('utf-8'))
                print(f"📨 {remitente} → {destinatario}: {mensaje}")
                
            else:
                self.clientes[remitente]['socket'].send("ERROR|Usuario no encontrado o desconectado".encode('utf-8'))
                
        except Exception as e:
            print(f"❌ Error enviando mensaje privado: {e}")
    
    def manejar_mensaje_general(self, mensaje, remitente):
        """Maneja mensajes del chat general"""
        if not remitente or remitente not in self.clientes:
            return None
        
        print(f"📢 {remitente} (general): {mensaje}")
        
        # NUEVO: Agregar mensaje al historial
        timestamp = datetime.now().strftime("%H:%M:%S")
        mensaje_con_timestamp = {
            'timestamp': timestamp,
            'remitente': remitente,
            'mensaje': mensaje
        }
        
        self.historial_general.append(mensaje_con_timestamp)
        
        # Mantener solo los últimos N mensajes
        if len(self.historial_general) > self.max_historial:
            self.historial_general.pop(0)
        
        # Enviar a todos los clientes conectados
        mensaje_formateado = f"BROADCAST_MSG|{remitente}|{mensaje}"
        clientes_desconectados = []
        
        for nombre, info in self.clientes.items():
            if info['conectado'] and nombre != remitente:  # No reenviar al remitente
                try:
                    info['socket'].send(mensaje_formateado.encode('utf-8'))
                except:
                    clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            del self.clientes[nombre]
        
        # Confirmar envío
        try:
            self.clientes[remitente]['socket'].send("SUCCESS|Mensaje enviado al chat general".encode('utf-8'))
        except:
            pass
    
    def enviar_lista_usuarios(self, cliente_socket):
        """Envía la lista de usuarios conectados"""
        usuarios = list(self.clientes.keys())
        lista_usuarios = ','.join(usuarios)
        mensaje = f"USER_LIST|{lista_usuarios}"
        cliente_socket.send(mensaje.encode('utf-8'))
    
    def enviar_historial_general(self, cliente_socket):
        """NUEVO: Envía el historial del chat general al cliente"""
        try:
            for msg in self.historial_general:
                mensaje_formateado = f"HISTORY_MSG|{msg['remitente']}|{msg['mensaje']}"
                cliente_socket.send(mensaje_formateado.encode('utf-8'))
                time.sleep(0.01)  # Pequeña pausa para evitar saturar
            
            # Señal de fin de historial
            cliente_socket.send("HISTORY_END|".encode('utf-8'))
        except Exception as e:
            print(f"❌ Error enviando historial: {e}")
    
    def notificar_cambio_usuarios(self):
        """Notifica a todos los clientes sobre cambios en la lista de usuarios"""
        usuarios = list(self.clientes.keys())
        lista_usuarios = ','.join(usuarios)
        mensaje = f"USER_UPDATE|{lista_usuarios}"
        
        clientes_desconectados = []
        for nombre, info in self.clientes.items():
            try:
                info['socket'].send(mensaje.encode('utf-8'))
            except:
                clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            del self.clientes[nombre]
    
    def notificar_usuario_entro(self, nombre_usuario):
        """NUEVO: Notifica a todos que un usuario se unió al chat"""
        mensaje = f"USER_JOINED|{nombre_usuario}"
        clientes_desconectados = []
        
        for nombre, info in self.clientes.items():
            if nombre != nombre_usuario:  # No notificar al usuario que acaba de entrar
                try:
                    info['socket'].send(mensaje.encode('utf-8'))
                except:
                    clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            del self.clientes[nombre]
    
    def notificar_usuario_salio(self, nombre_usuario):
        """NUEVO: Notifica a todos que un usuario salió del chat"""
        mensaje = f"USER_LEFT|{nombre_usuario}"
        clientes_desconectados = []
        
        for nombre, info in self.clientes.items():
            if nombre != nombre_usuario:  # Por si acaso
                try:
                    info['socket'].send(mensaje.encode('utf-8'))
                except:
                    clientes_desconectados.append(nombre)
        
        # Limpiar clientes desconectados
        for nombre in clientes_desconectados:
            if nombre in self.clientes:
                del self.clientes[nombre]
    
    def detener_servidor(self):
        """Detiene el servidor y cierra todas las conexiones"""
        print("🛑 Cerrando servidor...")
        self.ejecutando = False
        
        # Cerrar todas las conexiones
        for info in self.clientes.values():
            try:
                info['socket'].close()
            except:
                pass
        
        # Cerrar socket servidor
        if self.socket_servidor:
            try:
                self.socket_servidor.close()
            except:
                pass
        
        print("✅ Servidor cerrado")

if __name__ == "__main__":
    servidor = ServidorChat()
    
    try:
        servidor.iniciar_servidor()
    except KeyboardInterrupt:
        servidor.detener_servidor()