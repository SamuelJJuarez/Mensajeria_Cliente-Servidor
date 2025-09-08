import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import socket
import threading
import time

class ClienteChat:
    def __init__(self):
        self.socket_cliente = None
        self.conectado = False
        self.nombre_usuario = ""
        self.host_servidor = ""
        self.puerto_servidor = 12345
        
        # Variables para la interfaz
        self.root = None
        self.usuarios_listbox = None
        self.chat_text = None
        self.mensaje_entry = None
        self.destinatario_var = None
        self.mensajes_privados = {}  # {usuario: [mensajes]}
        self.mensajes_generales = []
        
        self.mostrar_ventana_conexion()
    
    def mostrar_ventana_conexion(self):
        """Muestra la ventana inicial para configurar la conexión"""
        ventana_conexion = tk.Tk()
        ventana_conexion.title("🔗 Conectar al Chat")
        ventana_conexion.geometry("400x300")
        ventana_conexion.resizable(False, False)
        
        # Centrar ventana
        ventana_conexion.eval('tk::PlaceWindow . center')
        
        # Título
        titulo = tk.Label(ventana_conexion, text="💬 Cliente de Chat", 
                         font=("Arial", 16, "bold"))
        titulo.pack(pady=20)
        
        # Frame para los campos
        frame_campos = tk.Frame(ventana_conexion)
        frame_campos.pack(pady=20, padx=40, fill="x")
        
        # Nombre de usuario
        tk.Label(frame_campos, text="👤 Nombre de usuario:", font=("Arial", 10)).pack(anchor="w")
        self.entry_nombre = tk.Entry(frame_campos, font=("Arial", 12))
        self.entry_nombre.pack(fill="x", pady=(5, 15))
        
        # IP del servidor
        tk.Label(frame_campos, text="🌐 IP del servidor:", font=("Arial", 10)).pack(anchor="w")
        self.entry_ip = tk.Entry(frame_campos, font=("Arial", 12))
        self.entry_ip.insert(0, "localhost")
        self.entry_ip.pack(fill="x", pady=(5, 15))
        
        # Puerto del servidor
        tk.Label(frame_campos, text="🔌 Puerto del servidor:", font=("Arial", 10)).pack(anchor="w")
        self.entry_puerto = tk.Entry(frame_campos, font=("Arial", 12))
        self.entry_puerto.insert(0, "12345")
        self.entry_puerto.pack(fill="x", pady=(5, 15))
        
        # Botón conectar
        btn_conectar = tk.Button(frame_campos, text="🚀 Conectar", 
                               font=("Arial", 12, "bold"),
                               bg="#4CAF50", fg="white",
                               command=lambda: self.intentar_conexion(ventana_conexion))
        btn_conectar.pack(pady=20, fill="x")
        
        # Permitir conectar con Enter
        ventana_conexion.bind('<Return>', lambda e: self.intentar_conexion(ventana_conexion))
        
        ventana_conexion.mainloop()
    
    def intentar_conexion(self, ventana_conexion):
        """Intenta conectarse al servidor con los datos ingresados"""
        nombre = self.entry_nombre.get().strip()
        ip = self.entry_ip.get().strip()
        puerto = self.entry_puerto.get().strip()
        
        if not nombre:
            messagebox.showerror("Error", "Por favor ingresa tu nombre de usuario")
            return
        
        if not ip:
            ip = "localhost"
        
        try:
            puerto = int(puerto) if puerto else 12345
        except ValueError:
            messagebox.showerror("Error", "Puerto inválido")
            return
        
        # Guardar datos
        self.nombre_usuario = nombre
        self.host_servidor = ip
        self.puerto_servidor = puerto
        
        # Intentar conectar
        if self.conectar_servidor():
            ventana_conexion.destroy()
            self.mostrar_ventana_chat()
        else:
            messagebox.showerror("Error de Conexión", 
                               "No se pudo conectar al servidor.\n"
                               "Verifica que esté ejecutándose y los datos sean correctos.")
    
    def conectar_servidor(self):
        """Conecta al servidor usando nuestro protocolo"""
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.host_servidor, self.puerto_servidor))
            
            # Enviar comando de conexión según nuestro protocolo
            comando_conexion = f"CONNECT|{self.nombre_usuario}"
            self.socket_cliente.send(comando_conexion.encode('utf-8'))
            
            # Esperar respuesta
            respuesta = self.socket_cliente.recv(1024).decode('utf-8')
            
            if respuesta.startswith("SUCCESS"):
                self.conectado = True
                
                # Iniciar hilo para recibir mensajes
                hilo_recibir = threading.Thread(target=self.recibir_mensajes)
                hilo_recibir.daemon = True
                hilo_recibir.start()
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error conectando: {e}")
            return False
    
    def mostrar_ventana_chat(self):
        """Muestra la ventana principal del chat"""
        self.root = tk.Tk()
        self.root.title(f"💬 Chat - {self.nombre_usuario}")
        self.root.geometry("800x600")
        
        # Crear layout principal
        self.crear_interfaz_chat()
        
        # Solicitar lista inicial de usuarios
        self.solicitar_usuarios()
        
        # Actualizar usuarios cada 3 segundos
        self.actualizar_usuarios_periodicamente()
        
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)
        self.root.mainloop()
    
    def crear_interfaz_chat(self):
        """Crea la interfaz gráfica del chat"""
        
        # Frame principal dividido en dos columnas
        frame_principal = tk.Frame(self.root)
        frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ================ COLUMNA IZQUIERDA (Usuarios) ================
        frame_usuarios = tk.LabelFrame(frame_principal, text="👥 Usuarios Conectados", 
                                     font=("Arial", 12, "bold"))
        frame_usuarios.pack(side="left", fill="y", padx=(0, 10))
        
        # Lista de usuarios
        self.usuarios_listbox = tk.Listbox(frame_usuarios, width=20, 
                                          font=("Arial", 10))
        self.usuarios_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ================ COLUMNA DERECHA (Chat) ================
        frame_chat = tk.Frame(frame_principal)
        frame_chat.pack(side="right", fill="both", expand=True)
        
        # Selector de destinatario
        frame_destinatario = tk.Frame(frame_chat)
        frame_destinatario.pack(fill="x", pady=(0, 10))
        
        tk.Label(frame_destinatario, text="💬 Chatear con:", 
                font=("Arial", 11)).pack(side="left")
        
        self.destinatario_var = tk.StringVar(value="🌐 Chat General")
        combo_destinatario = ttk.Combobox(frame_destinatario, 
                                         textvariable=self.destinatario_var,
                                         state="readonly",
                                         font=("Arial", 10))
        combo_destinatario.pack(side="left", padx=(10, 0), fill="x", expand=True)
        combo_destinatario.bind('<<ComboboxSelected>>', self.cambiar_chat)
        
        self.combo_destinatario = combo_destinatario  # Guardar referencia
        
        # Área de mensajes
        frame_mensajes = tk.LabelFrame(frame_chat, text="💭 Mensajes")
        frame_mensajes.pack(fill="both", expand=True, pady=(0, 10))
        
        # Crear área de texto con scrollbar
        frame_text = tk.Frame(frame_mensajes)
        frame_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.chat_text = tk.Text(frame_text, state="disabled", 
                                font=("Arial", 10),
                                wrap="word")
        scrollbar = tk.Scrollbar(frame_text, orient="vertical", 
                               command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=scrollbar.set)
        
        self.chat_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Área de envío
        frame_envio = tk.Frame(frame_chat)
        frame_envio.pack(fill="x")
        
        self.mensaje_entry = tk.Entry(frame_envio, font=("Arial", 11))
        self.mensaje_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_enviar = tk.Button(frame_envio, text="📤 Enviar", 
                             font=("Arial", 11, "bold"),
                             bg="#2196F3", fg="white",
                             command=self.enviar_mensaje)
        btn_enviar.pack(side="right")
        
        # Permitir enviar con Enter
        self.mensaje_entry.bind('<Return>', lambda e: self.enviar_mensaje())
    
    def recibir_mensajes(self):
        """Hilo para recibir mensajes del servidor"""
        while self.conectado:
            try:
                mensaje = self.socket_cliente.recv(4096).decode('utf-8')
                if not mensaje:
                    break
                
                self.procesar_mensaje_recibido(mensaje)
                
            except Exception as e:
                if self.conectado:
                    print(f"Error recibiendo mensaje: {e}")
                break
    
    def procesar_mensaje_recibido(self, mensaje):
        """Procesa mensajes recibidos según nuestro protocolo"""
        try:
            partes = mensaje.split('|', 2)
            comando = partes[0]
            
            if comando == "USER_UPDATE" or comando == "USER_LIST":
                usuarios_texto = partes[1] if len(partes) > 1 else ""
                self.actualizar_lista_usuarios(usuarios_texto)
            
            elif comando == "PRIVATE_MSG":
                remitente = partes[1]
                contenido = partes[2] if len(partes) > 2 else ""
                self.recibir_mensaje_privado(remitente, contenido)
            
            elif comando == "BROADCAST_MSG":
                remitente = partes[1]
                contenido = partes[2] if len(partes) > 2 else ""
                self.recibir_mensaje_general(remitente, contenido)
            
            elif comando == "SUCCESS":
                pass  # Mensaje enviado exitosamente
            
            elif comando == "ERROR":
                error_msg = partes[1] if len(partes) > 1 else "Error desconocido"
                self.mostrar_error(error_msg)
                
        except Exception as e:
            print(f"Error procesando mensaje: {e}")
    
    def actualizar_lista_usuarios(self, usuarios_texto):
        """Actualiza la lista de usuarios conectados"""
        if not self.usuarios_listbox:
            return
        
        usuarios = [u.strip() for u in usuarios_texto.split(',') if u.strip()]
        
        # Actualizar listbox en el hilo principal
        self.root.after(0, self._actualizar_listbox_usuarios, usuarios)
    
    def _actualizar_listbox_usuarios(self, usuarios):
        """Actualiza el listbox de usuarios (debe ejecutarse en hilo principal)"""
        # Limpiar lista actual
        self.usuarios_listbox.delete(0, tk.END)
        
        # Agregar usuarios (excepto el propio)
        otros_usuarios = [u for u in usuarios if u != self.nombre_usuario]
        for usuario in otros_usuarios:
            self.usuarios_listbox.insert(tk.END, f"👤 {usuario}")
        
        # Actualizar combobox de destinatarios
        valores = ["🌐 Chat General"] + [f"👤 {u}" for u in otros_usuarios]
        self.combo_destinatario['values'] = valores
    
    def recibir_mensaje_privado(self, remitente, contenido):
        """Maneja mensajes privados recibidos"""
        if remitente not in self.mensajes_privados:
            self.mensajes_privados[remitente] = []
        
        timestamp = time.strftime("%H:%M:%S")
        mensaje_formateado = f"[{timestamp}] {remitente}: {contenido}"
        self.mensajes_privados[remitente].append(mensaje_formateado)
        
        # Si estamos viendo el chat de esta persona, actualizar
        destinatario_actual = self.destinatario_var.get()
        if destinatario_actual == f"👤 {remitente}":
            self.root.after(0, self.actualizar_area_chat)
    
    def recibir_mensaje_general(self, remitente, contenido):
        """Maneja mensajes del chat general"""
        timestamp = time.strftime("%H:%M:%S")
        mensaje_formateado = f"[{timestamp}] {remitente}: {contenido}"
        self.mensajes_generales.append(mensaje_formateado)
        
        # Si estamos viendo el chat general, actualizar
        if self.destinatario_var.get() == "🌐 Chat General":
            self.root.after(0, self.actualizar_area_chat)
    
    def cambiar_chat(self, event=None):
        """Cambia entre diferentes chats"""
        self.actualizar_area_chat()
    
    def actualizar_area_chat(self):
        """Actualiza el área de mensajes según el chat seleccionado"""
        if not self.chat_text:
            return
        
        destinatario = self.destinatario_var.get()
        
        # Limpiar área de chat
        self.chat_text.config(state="normal")
        self.chat_text.delete(1.0, tk.END)
        
        if destinatario == "🌐 Chat General":
            # Mostrar mensajes generales
            for mensaje in self.mensajes_generales:
                self.chat_text.insert(tk.END, mensaje + "\n")
        else:
            # Obtener nombre del usuario (quitar emoji)
            nombre_usuario = destinatario.replace("👤 ", "")
            
            # Mostrar mensajes privados con este usuario
            if nombre_usuario in self.mensajes_privados:
                for mensaje in self.mensajes_privados[nombre_usuario]:
                    self.chat_text.insert(tk.END, mensaje + "\n")
        
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)  # Scroll hasta abajo
    
    def enviar_mensaje(self):
        """Envía mensaje según el destinatario seleccionado"""
        if not self.conectado:
            return
        
        mensaje = self.mensaje_entry.get().strip()
        if not mensaje:
            return
        
        destinatario = self.destinatario_var.get()
        
        if destinatario == "🌐 Chat General":
            # Enviar mensaje general
            comando = f"BROADCAST|{mensaje}"
        else:
            # Enviar mensaje privado
            nombre_destinatario = destinatario.replace("👤 ", "")
            comando = f"MESSAGE|{nombre_destinatario}|{mensaje}"
        
        try:
            self.socket_cliente.send(comando.encode('utf-8'))
            
            # Limpiar campo de entrada
            self.mensaje_entry.delete(0, tk.END)
            
            # Agregar mensaje enviado a nuestra vista
            timestamp = time.strftime("%H:%M:%S")
            if destinatario == "🌐 Chat General":
                mensaje_formateado = f"[{timestamp}] Tú: {mensaje}"
                self.mensajes_generales.append(mensaje_formateado)
            else:
                nombre_destinatario = destinatario.replace("👤 ", "")
                if nombre_destinatario not in self.mensajes_privados:
                    self.mensajes_privados[nombre_destinatario] = []
                mensaje_formateado = f"[{timestamp}] Tú: {mensaje}"
                self.mensajes_privados[nombre_destinatario].append(mensaje_formateado)
            
            # Actualizar vista
            self.actualizar_area_chat()
            
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
            messagebox.showerror("Error", "No se pudo enviar el mensaje")
    
    def solicitar_usuarios(self):
        """Solicita la lista de usuarios al servidor"""
        if self.conectado:
            try:
                self.socket_cliente.send("GET_USERS|".encode('utf-8'))
            except:
                pass
    
    def actualizar_usuarios_periodicamente(self):
        """Actualiza la lista de usuarios cada pocos segundos"""
        if self.conectado:
            self.solicitar_usuarios()
            self.root.after(3000, self.actualizar_usuarios_periodicamente)  # Cada 3 segundos
    
    def mostrar_error(self, mensaje):
        """Muestra un error al usuario"""
        self.root.after(0, lambda: messagebox.showerror("Error", mensaje))
    
    def cerrar_aplicacion(self):
        """Cierra la aplicación correctamente"""
        self.conectado = False
        
        if self.socket_cliente:
            try:
                self.socket_cliente.close()
            except:
                pass
        
        if self.root:
            self.root.destroy()

if __name__ == "__main__":
    cliente = ClienteChat()