package Topicos_despliegue.Servidor_cliente;

import javax.swing.*;
import javax.swing.Timer;
import javax.swing.border.EmptyBorder;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.KeyAdapter;
import java.awt.event.KeyEvent;
import java.io.*;
import java.net.Socket;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;


public class ClienteChat extends JFrame {
    // Conexión
    private Socket socketCliente;
    private PrintWriter escritor;
    private BufferedReader lector;
    private boolean conectado = false;
    private String nombreUsuario = "";
    private String hostServidor = "localhost";
    private int puertoServidor = 12345;
    
    // Interfaz gráfica
    private JList<String> listaUsuarios;
    private DefaultListModel<String> modeloUsuarios;
    private JTextArea areaMensajes;
    private JTextField campoMensaje;
    private JComboBox<String> comboDestinatario;
    private JLabel labelNotificaciones;
    private JLabel labelEstado;
    
    // Datos del chat
    private Map<String, java.util.List<String>> mensajesPrivados;
    private java.util.List<String> mensajesGenerales;
    private Set<String> usuariosConMensajesNuevos;
    
    // Buffer para mensajes
    private StringBuilder bufferMensajes;
    
    // Ventana de notificación
    private JWindow ventanaNotificacion;
    
    public ClienteChat() {
        this.mensajesPrivados = new ConcurrentHashMap<>();
        this.mensajesGenerales = new ArrayList<>();
        this.usuariosConMensajesNuevos = new HashSet<>();
        this.bufferMensajes = new StringBuilder();
        
        mostrarVentanaConexion();
    }
    
    private void mostrarVentanaConexion() {
        JDialog ventanaConexion = new JDialog(this, "Conectar al Chat", true);
        ventanaConexion.setSize(450, 350);
        ventanaConexion.setLocationRelativeTo(null);
        ventanaConexion.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
        
        // Panel principal
        JPanel panelPrincipal = new JPanel(new BorderLayout());
        panelPrincipal.setBorder(new EmptyBorder(20, 20, 20, 20));
        
        // Título
        JLabel titulo = new JLabel("Cliente de Chat", JLabel.CENTER);
        titulo.setFont(new Font("Arial", Font.BOLD, 18));
        titulo.setBorder(new EmptyBorder(0, 0, 20, 0));
        panelPrincipal.add(titulo, BorderLayout.NORTH);
        
        // Panel de campos
        JPanel panelCampos = new JPanel(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(5, 5, 5, 5);
        gbc.anchor = GridBagConstraints.WEST;
        
        // Nombre de usuario
        gbc.gridx = 0; gbc.gridy = 0;
        panelCampos.add(new JLabel("Nombre de usuario:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        JTextField campoNombre = new JTextField(20);
        panelCampos.add(campoNombre, gbc);
        
        // IP del servidor
        gbc.gridx = 0; gbc.gridy = 1; gbc.fill = GridBagConstraints.NONE;
        panelCampos.add(new JLabel("IP del servidor:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        JTextField campoIP = new JTextField("localhost", 20);
        panelCampos.add(campoIP, gbc);
        
        // Puerto del servidor
        gbc.gridx = 0; gbc.gridy = 2; gbc.fill = GridBagConstraints.NONE;
        panelCampos.add(new JLabel("Puerto del servidor:"), gbc);
        gbc.gridx = 1; gbc.fill = GridBagConstraints.HORIZONTAL;
        JTextField campoPuerto = new JTextField("12345", 20);
        panelCampos.add(campoPuerto, gbc);
        
        panelPrincipal.add(panelCampos, BorderLayout.CENTER);
        
        // Panel de botones
        JPanel panelBotones = new JPanel(new FlowLayout());
        JButton btnConectar = new JButton("Conectar");
        btnConectar.setBackground(new Color(76, 175, 80));
        btnConectar.setForeground(Color.WHITE);
        btnConectar.setFont(new Font("Arial", Font.BOLD, 12));
        
        JButton btnCancelar = new JButton("Cancelar");
        btnCancelar.setBackground(new Color(244, 67, 54));
        btnCancelar.setForeground(Color.WHITE);
        
        panelBotones.add(btnConectar);
        panelBotones.add(btnCancelar);
        panelPrincipal.add(panelBotones, BorderLayout.SOUTH);
        
        // Eventos
        btnConectar.addActionListener(e -> {
            if (intentarConexion(campoNombre.getText().trim(), 
                                campoIP.getText().trim(), 
                                campoPuerto.getText().trim())) {
                ventanaConexion.dispose();
                mostrarVentanaChat();
            }
        });
        
        btnCancelar.addActionListener(e -> {
            ventanaConexion.dispose();
            System.exit(0);
        });
        
        // Enter para conectar
        KeyAdapter enterListener = new KeyAdapter() {
            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_ENTER) {
                    btnConectar.doClick();
                }
            }
        };
        
        campoNombre.addKeyListener(enterListener);
        campoIP.addKeyListener(enterListener);
        campoPuerto.addKeyListener(enterListener);
        
        ventanaConexion.add(panelPrincipal);
        ventanaConexion.setVisible(true);
    }
    
    private boolean intentarConexion(String nombre, String ip, String puerto) {
        if (nombre.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Por favor ingresa tu nombre de usuario", "Error", JOptionPane.ERROR_MESSAGE);
            return false;
        }
        if (ip.isEmpty()) {
            ip = "localhost";
        }
        
        try {
            int puertoInt = puerto.isEmpty() ? 12345 : Integer.parseInt(puerto);
            this.nombreUsuario = nombre;
            this.hostServidor = ip;
            this.puertoServidor = puertoInt;
            return conectarServidor();
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Puerto inválido", "Error", JOptionPane.ERROR_MESSAGE);
            return false;
        }
    }
    
    private boolean conectarServidor() {
        try {
            socketCliente = new Socket(hostServidor, puertoServidor);
            escritor = new PrintWriter(socketCliente.getOutputStream(), true);
            lector = new BufferedReader(new InputStreamReader(socketCliente.getInputStream()));
            // Enviar comando de conexión
            String comandoConexion = "CONNECT|" + nombreUsuario;
            escritor.println(comandoConexion);
            // Esperar respuesta
            String respuesta = lector.readLine();
            if (respuesta != null && respuesta.startsWith("SUCCESS")) {
                conectado = true;  
                // Iniciar hilo para recibir mensajes
                Thread hiloReceptor = new Thread(this::recibirMensajes);
                hiloReceptor.setDaemon(true);
                hiloReceptor.start();
                return true;
            } else {
                return false;
            }
            
        } catch (Exception e) {
            System.err.println("Error conectando: " + e.getMessage());
            JOptionPane.showMessageDialog(this,  "No se pudo conectar al servidor.\nVerifica que esté ejecutándose y los datos sean correctos.",
                "Error de Conexión", JOptionPane.ERROR_MESSAGE);
            return false;
        }
    }
    
    private void mostrarVentanaChat() {
        setTitle("Chat - " + nombreUsuario);
        setSize(900, 650);
        setLocationRelativeTo(null);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        crearInterfazChat();
        // Solicitar datos iniciales
        solicitarUsuarios();
        solicitarHistorial();
        // Actualizar usuarios periódicamente
        Timer timerUsuarios = new Timer(3000, e -> solicitarUsuarios());
        timerUsuarios.start();
        setVisible(true);
    }
    
    private void crearInterfazChat() {
        setLayout(new BorderLayout());
        // Panel principal
        JSplitPane panelPrincipal = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        panelPrincipal.setDividerLocation(200);
        
        // ========== PANEL IZQUIERDO (Usuarios) ==========
        JPanel panelUsuarios = new JPanel(new BorderLayout());
        panelUsuarios.setBorder(new TitledBorder("Usuarios Conectados"));
        panelUsuarios.setPreferredSize(new Dimension(200, 0));
        
        // Lista de usuarios
        modeloUsuarios = new DefaultListModel<>();
        listaUsuarios = new JList<>(modeloUsuarios);
        listaUsuarios.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        listaUsuarios.setFont(new Font("Monospaced", Font.PLAIN, 12));
        JScrollPane scrollUsuarios = new JScrollPane(listaUsuarios);
        panelUsuarios.add(scrollUsuarios, BorderLayout.CENTER);
        
        // Label de notificaciones
        labelNotificaciones = new JLabel(" ");
        labelNotificaciones.setFont(new Font("Arial", Font.ITALIC, 10));
        labelNotificaciones.setForeground(Color.GREEN);
        panelUsuarios.add(labelNotificaciones, BorderLayout.SOUTH);
        panelPrincipal.setLeftComponent(panelUsuarios);
        
        // ========== PANEL DERECHO (Chat) ==========
        JPanel panelChat = new JPanel(new BorderLayout());
        
        // Panel superior con selector de destinatario
        JPanel panelSuperior = new JPanel(new BorderLayout());
        panelSuperior.setBorder(new EmptyBorder(5, 5, 5, 5));
        JLabel labelDestinatario = new JLabel("Chatear con: ");
        comboDestinatario = new JComboBox<>();
        comboDestinatario.addItem("Chat General");
        comboDestinatario.addActionListener(e -> cambiarChat());
        
        // Label de estado de conexión
        labelEstado = new JLabel("Conectado a " + hostServidor + ":" + puertoServidor);
        labelEstado.setFont(new Font("Arial", Font.PLAIN, 10));
        labelEstado.setForeground(Color.BLUE);
        panelSuperior.add(labelDestinatario, BorderLayout.WEST);
        panelSuperior.add(comboDestinatario, BorderLayout.CENTER);
        panelSuperior.add(labelEstado, BorderLayout.EAST);
        panelChat.add(panelSuperior, BorderLayout.NORTH);
        
        // Área de mensajes
        areaMensajes = new JTextArea();
        areaMensajes.setEditable(false);
        areaMensajes.setFont(new Font("Monospaced", Font.PLAIN, 12));
        areaMensajes.setBackground(new Color(248, 248, 248));
        areaMensajes.setLineWrap(true);
        areaMensajes.setWrapStyleWord(true);
        
        JScrollPane scrollMensajes = new JScrollPane(areaMensajes);
        scrollMensajes.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        scrollMensajes.setBorder(new TitledBorder("Mensajes"));
        panelChat.add(scrollMensajes, BorderLayout.CENTER);
        
        // Panel de envío
        JPanel panelEnvio = new JPanel(new BorderLayout());
        panelEnvio.setBorder(new EmptyBorder(5, 5, 5, 5));
        campoMensaje = new JTextField();
        campoMensaje.setFont(new Font("Arial", Font.PLAIN, 12));
        campoMensaje.addKeyListener(new KeyAdapter() {
            @Override
            public void keyPressed(KeyEvent e) {
                if (e.getKeyCode() == KeyEvent.VK_ENTER) {
                    enviarMensaje();
                }
            }
        });
        
        JButton btnEnviar = new JButton("Enviar");
        btnEnviar.setBackground(new Color(33, 150, 243));
        btnEnviar.setForeground(Color.WHITE);
        btnEnviar.setFont(new Font("Arial", Font.BOLD, 12));
        btnEnviar.addActionListener(e -> enviarMensaje());
        panelEnvio.add(campoMensaje, BorderLayout.CENTER);
        panelEnvio.add(btnEnviar, BorderLayout.EAST);
        panelChat.add(panelEnvio, BorderLayout.SOUTH);
        panelPrincipal.setRightComponent(panelChat);
        add(panelPrincipal, BorderLayout.CENTER);
        
        // Panel de estado en la parte inferior
        JPanel panelEstado = new JPanel(new FlowLayout(FlowLayout.LEFT));
        panelEstado.setBackground(new Color(230, 230, 230));
        JLabel labelInfo = new JLabel("Usuario: " + nombreUsuario + " | ");
        labelInfo.setFont(new Font("Arial", Font.PLAIN, 11));
        panelEstado.add(labelInfo);
        add(panelEstado, BorderLayout.SOUTH);
    }
    
    private void recibirMensajes() {
        char[] buffer = new char[4096];
        while (conectado) {
            try {
                int leidos = lector.read(buffer);
                if (leidos == -1) break;
                String data = new String(buffer, 0, leidos);
                bufferMensajes.append(data);
                procesarBufferMensajes();
            } catch (Exception e) {
                if (conectado) {
                    System.err.println("Error recibiendo mensaje: " + e.getMessage());
                }
                break;
            }
        }
    }
    
    private void procesarBufferMensajes() {
        String[] comandos = {"USER_UPDATE|", "USER_LIST|", "PRIVATE_MSG|", "BROADCAST_MSG|", 
                           "HISTORY_MSG|", "HISTORY_END|", "USER_JOINED|", "USER_LEFT|", 
                           "SUCCESS|", "ERROR|", "PONG"};
        String contenido = bufferMensajes.toString();
        while (true) {
            boolean encontrado = false;
            int posicionSiguiente = contenido.length();
            for (String cmd : comandos) {
                int pos = contenido.indexOf(cmd);
                if (pos != -1) {
                    if (pos > 0) {
                        for (String cmd2 : comandos) {
                            int pos2 = contenido.indexOf(cmd2, pos + cmd.length());
                            if (pos2 != -1) {
                                posicionSiguiente = pos2;
                                break;
                            }
                        }
                        String mensajeCompleto = contenido.substring(0, posicionSiguiente);
                        bufferMensajes = new StringBuilder(contenido.substring(posicionSiguiente));
                        separarYProcesarMensajes(mensajeCompleto);
                        contenido = bufferMensajes.toString();
                        encontrado = true;
                        break;
                    } else {
                        for (String cmd2 : comandos) {
                            int pos2 = contenido.indexOf(cmd2, cmd.length());
                            if (pos2 != -1) {
                                posicionSiguiente = pos2;
                                break;
                            }
                        }
                        
                        if (posicionSiguiente < contenido.length()) {
                            String mensajeCompleto = contenido.substring(0, posicionSiguiente);
                            bufferMensajes = new StringBuilder(contenido.substring(posicionSiguiente));
                            procesarMensajeRecibido(mensajeCompleto);
                            contenido = bufferMensajes.toString();
                            encontrado = true;
                            break;
                        }
                    }
                }
            }
            
            if (!encontrado) {
                if (!contenido.isEmpty()) {
                    for (String cmd : comandos) {
                        if (contenido.startsWith(cmd.split("\\|")[0])) {
                            procesarMensajeRecibido(contenido);
                            bufferMensajes = new StringBuilder();
                            break;
                        }
                    }
                }
                break;
            }
        }
    }
    
    private void separarYProcesarMensajes(String contenido) {
        String[] comandos = {"USER_UPDATE|", "USER_LIST|", "PRIVATE_MSG|", "BROADCAST_MSG|", 
                           "HISTORY_MSG|", "HISTORY_END|", "USER_JOINED|", "USER_LEFT|", 
                           "SUCCESS|", "ERROR|"};
        
        java.util.List<String> mensajes = new ArrayList<>();
        int inicio = 0;
        
        for (int i = 1; i < contenido.length(); i++) {
            for (String cmd : comandos) {
                if (i + cmd.length() <= contenido.length() && 
                    contenido.substring(i, i + cmd.length()).equals(cmd)) {
                    String mensaje = contenido.substring(inicio, i);
                    if (!mensaje.trim().isEmpty()) {
                        mensajes.add(mensaje);
                    }
                    inicio = i;
                    break;
                }
            }
        }
        
        if (inicio < contenido.length()) {
            String mensaje = contenido.substring(inicio);
            if (!mensaje.trim().isEmpty()) {
                mensajes.add(mensaje);
            }
        }
        
        for (String mensaje : mensajes) {
            procesarMensajeRecibido(mensaje.trim());
        }
    }
    
    private void procesarMensajeRecibido(String mensaje) {
        try {
            String[] partes = mensaje.split("\\|", 3);
            String comando = partes[0];
            
            switch (comando) {
                case "USER_UPDATE":
                case "USER_LIST":
                    String usuariosTexto = partes.length > 1 ? partes[1] : "";
                    SwingUtilities.invokeLater(() -> actualizarListaUsuarios(usuariosTexto));
                    break;
                    
                case "PRIVATE_MSG":
                    if (partes.length >= 3) {
                        String remitente = partes[1];
                        String contenido = partes[2];
                        SwingUtilities.invokeLater(() -> recibirMensajePrivado(remitente, contenido));
                    }
                    break;
                    
                case "BROADCAST_MSG":
                    if (partes.length >= 3) {
                        String remitente = partes[1];
                        String contenido = partes[2];
                        SwingUtilities.invokeLater(() -> recibirMensajeGeneral(remitente, contenido));
                    }
                    break;
                    
                case "HISTORY_MSG":
                    if (partes.length >= 3) {
                        String remitente = partes[1];
                        String contenido = partes[2];
                        SwingUtilities.invokeLater(() -> recibirMensajeHistorial(remitente, contenido));
                    }
                    break;
                    
                case "HISTORY_END":
                    SwingUtilities.invokeLater(this::finalizarCargaHistorial);
                    break;
                    
                case "USER_JOINED":
                    if (partes.length >= 2) {
                        String nombreUsuario = partes[1];
                        SwingUtilities.invokeLater(() -> mostrarNotificacionUsuarioEntro(nombreUsuario));
                    }
                    break;
                    
                case "USER_LEFT":
                    if (partes.length >= 2) {
                        String nombreUsuario = partes[1];
                        SwingUtilities.invokeLater(() -> mostrarNotificacionUsuarioSalio(nombreUsuario));
                    }
                    break;
                    
                case "SUCCESS":
                    // Mensaje enviado exitosamente
                    break;
                    
                case "ERROR":
                    String errorMsg = partes.length > 1 ? partes[1] : "Error desconocido";
                    SwingUtilities.invokeLater(() -> mostrarError(errorMsg));
                    break;
            }
            
        } catch (Exception e) {
            System.err.println("Error procesando mensaje: " + e.getMessage());
            System.err.println("Mensaje problemático: " + mensaje);
        }
    }
    
    private void actualizarListaUsuarios(String usuariosTexto) {
        String[] usuarios = usuariosTexto.split(",");
        
        modeloUsuarios.clear();
        comboDestinatario.removeAllItems();
        comboDestinatario.addItem("Chat General");
        
        for (String usuario : usuarios) {
            usuario = usuario.trim();
            if (!usuario.isEmpty() && !usuario.equals(nombreUsuario)) {
                String display = usuario;
                if (usuariosConMensajesNuevos.contains(usuario)) {
                    display = "(*) " + usuario;
                }
                
                modeloUsuarios.addElement(display);
                comboDestinatario.addItem(display);
            }
        }
    }
    
    private void recibirMensajePrivado(String remitente, String contenido) {
        if (!mensajesPrivados.containsKey(remitente)) {
            mensajesPrivados.put(remitente, new ArrayList<>());
        }
        
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        String mensajeFormateado = String.format("[%s] %s: %s", timestamp, remitente, contenido);
        mensajesPrivados.get(remitente).add(mensajeFormateado);
        
        // Marcar usuario con mensaje nuevo si no estamos viendo su chat
        String destinatarioActual = (String) comboDestinatario.getSelectedItem();
        if (!destinatarioActual.equals(remitente) && !destinatarioActual.equals("(*) " + remitente)) {
            usuariosConMensajesNuevos.add(remitente);
            solicitarUsuarios(); // Actualizar lista
            mostrarNotificacionMensajePrivado(remitente);
        }
        
        // Si estamos viendo el chat de esta persona, actualizar
        if (destinatarioActual.equals(remitente) || destinatarioActual.equals("(*) " + remitente)) {
            actualizarAreaChat();
        }
    }
    
    private void recibirMensajeGeneral(String remitente, String contenido) {
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        String mensajeFormateado = String.format("[%s] %s: %s", timestamp, remitente, contenido);
        mensajesGenerales.add(mensajeFormateado);
        
        // Si estamos viendo el chat general, actualizar
        if ("Chat General".equals(comboDestinatario.getSelectedItem())) {
            actualizarAreaChat();
        }
    }
    
    private void recibirMensajeHistorial(String remitente, String contenido) {
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        String mensajeFormateado = String.format("[%s] %s: %s", timestamp, remitente, contenido);
        mensajesGenerales.add(mensajeFormateado);
    }
    
    private void finalizarCargaHistorial() {
        if ("Chat General".equals(comboDestinatario.getSelectedItem())) {
            actualizarAreaChat();
        }
    }
    
    private void mostrarNotificacionUsuarioEntro(String nombreUsuario) {
        String mensaje = nombreUsuario + " se unió al chat";
        actualizarNotificacionTemporal(mensaje, Color.GREEN);
        
        // Agregar al chat general como mensaje del sistema
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        String mensajeSistema = String.format("[%s] SISTEMA: %s", timestamp, mensaje);
        mensajesGenerales.add(mensajeSistema);
        
        if ("Chat General".equals(comboDestinatario.getSelectedItem())) {
            actualizarAreaChat();
        }
    }
    
    private void mostrarNotificacionUsuarioSalio(String nombreUsuario) {
        String mensaje = nombreUsuario + " salió del chat";
        actualizarNotificacionTemporal(mensaje, Color.RED);
        
        // Agregar al chat general como mensaje del sistema
        String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
        String mensajeSistema = String.format("[%s] SISTEMA: %s", timestamp, mensaje);
        mensajesGenerales.add(mensajeSistema);
        
        // Limpiar mensajes nuevos de este usuario
        usuariosConMensajesNuevos.remove(nombreUsuario);
        
        if ("Chat General".equals(comboDestinatario.getSelectedItem())) {
            actualizarAreaChat();
        }
    }
    
    private void mostrarNotificacionMensajePrivado(String remitente) {
        if (ventanaNotificacion != null) {
            ventanaNotificacion.dispose();
        }
        
        ventanaNotificacion = new JWindow(this);
        ventanaNotificacion.setSize(280, 90);
        
        // Posicionar en esquina superior derecha
        int x = getX() + getWidth() - 300;
        int y = getY() + 30;
        ventanaNotificacion.setLocation(x, y);
        
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBackground(new Color(255, 228, 181));
        panel.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        
        JLabel labelTitulo = new JLabel("Nuevo mensaje privado", JLabel.CENTER);
        labelTitulo.setFont(new Font("Arial", Font.BOLD, 11));
        panel.add(labelTitulo, BorderLayout.NORTH);
        
        JLabel labelRemitente = new JLabel("De: " + remitente, JLabel.CENTER);
        labelRemitente.setFont(new Font("Arial", Font.PLAIN, 10));
        panel.add(labelRemitente, BorderLayout.CENTER);
        
        JPanel panelBotones = new JPanel(new FlowLayout());
        panelBotones.setBackground(new Color(255, 228, 181));
        
        JButton btnVer = new JButton("Ver");
        btnVer.setFont(new Font("Arial", Font.PLAIN, 9));
        btnVer.addActionListener(e -> irAChatPrivado(remitente));
        
        JButton btnCerrar = new JButton("Cerrar");
        btnCerrar.setFont(new Font("Arial", Font.PLAIN, 9));
        btnCerrar.addActionListener(e -> ventanaNotificacion.dispose());
        
        panelBotones.add(btnVer);
        panelBotones.add(btnCerrar);
        panel.add(panelBotones, BorderLayout.SOUTH);
        
        ventanaNotificacion.add(panel);
        ventanaNotificacion.setVisible(true);
        
        // Auto-cerrar después de 5 segundos
        Timer timer = new Timer(5000, e -> {
            if (ventanaNotificacion != null) {
                ventanaNotificacion.dispose();
            }
        });
        timer.setRepeats(false);
        timer.start();
    }
    
    private void irAChatPrivado(String nombreUsuario) {
        if (ventanaNotificacion != null) {
            ventanaNotificacion.dispose();
        }
        
        // Cambiar al chat del usuario
        String itemUsuario = nombreUsuario;
        if (usuariosConMensajesNuevos.contains(nombreUsuario)) {
            itemUsuario = "(*) " + nombreUsuario;
        }
        comboDestinatario.setSelectedItem(itemUsuario);
        
        // Marcar como leído
        usuariosConMensajesNuevos.remove(nombreUsuario);
        solicitarUsuarios();
        
        actualizarAreaChat();
    }
    
    private void actualizarNotificacionTemporal(String mensaje, Color color) {
        labelNotificaciones.setText(mensaje);
        labelNotificaciones.setForeground(color);
        
        Timer timer = new Timer(3000, e -> labelNotificaciones.setText(" "));
        timer.setRepeats(false);
        timer.start();
    }
    
    private void cambiarChat() {
        // Marcar mensajes como leídos al cambiar de chat
        String destinatario = (String) comboDestinatario.getSelectedItem();
        if (destinatario != null && destinatario.startsWith("(*) ")) {
            String nombreUsuario = destinatario.replace("(*) ", "");
            usuariosConMensajesNuevos.remove(nombreUsuario);
            solicitarUsuarios(); // Actualizar lista
        }
        
        actualizarAreaChat();
    }
    
    private void actualizarAreaChat() {
        String destinatario = (String) comboDestinatario.getSelectedItem();
        if (destinatario == null) return;
        
        areaMensajes.setText("");
        
        if ("Chat General".equals(destinatario)) {
            // Mostrar mensajes generales
            for (String mensaje : mensajesGenerales) {
                areaMensajes.append(mensaje + "\n");
            }
        } else {
            // Obtener nombre del usuario (quitar prefijo si lo tiene)
            String nombreUsuario = destinatario;
            if (destinatario.startsWith("(*) ")) {
                nombreUsuario = destinatario.replace("(*) ", "");
            }
            
            // Mostrar mensajes privados con este usuario
            if (mensajesPrivados.containsKey(nombreUsuario)) {
                for (String mensaje : mensajesPrivados.get(nombreUsuario)) {
                    areaMensajes.append(mensaje + "\n");
                }
            }
        }
        
        // Scroll hasta abajo
        areaMensajes.setCaretPosition(areaMensajes.getDocument().getLength());
    }
    
    private void enviarMensaje() {
        if (!conectado) return;
        
        String mensaje = campoMensaje.getText().trim();
        if (mensaje.isEmpty()) return;
        
        String destinatario = (String) comboDestinatario.getSelectedItem();
        if (destinatario == null) return;
        
        String comando;
        if ("Chat General".equals(destinatario)) {
            // Enviar mensaje general
            comando = "BROADCAST|" + mensaje;
        } else {
            // Enviar mensaje privado (quitar prefijo si lo tiene)
            String nombreDestinatario = destinatario;
            if (destinatario.startsWith("(*) ")) {
                nombreDestinatario = destinatario.replace("(*) ", "");
            }
            comando = "MESSAGE|" + nombreDestinatario + "|" + mensaje;
        }
        
        try {
            escritor.println(comando);
            
            // Limpiar campo de entrada
            campoMensaje.setText("");
            
            // Agregar mensaje enviado a nuestra vista
            String timestamp = new SimpleDateFormat("HH:mm:ss").format(new Date());
            if ("Chat General".equals(destinatario)) {
                String mensajeFormateado = String.format("[%s] Tú: %s", timestamp, mensaje);
                mensajesGenerales.add(mensajeFormateado);
            } else {
                String nombreDestinatario = destinatario;
                if (destinatario.startsWith("(*) ")) {
                    nombreDestinatario = destinatario.replace("(*) ", "");
                }
                
                if (!mensajesPrivados.containsKey(nombreDestinatario)) {
                    mensajesPrivados.put(nombreDestinatario, new ArrayList<>());
                }
                String mensajeFormateado = String.format("[%s] Tú: %s", timestamp, mensaje);
                mensajesPrivados.get(nombreDestinatario).add(mensajeFormateado);
            }
            
            // Actualizar vista
            actualizarAreaChat();
            
        } catch (Exception e) {
            System.err.println("Error enviando mensaje: " + e.getMessage());
            JOptionPane.showMessageDialog(this, "No se pudo enviar el mensaje", 
                                        "Error", JOptionPane.ERROR_MESSAGE);
        }
    }
    
    private void solicitarUsuarios() {
        if (conectado && escritor != null) {
            try {
                escritor.println("GET_USERS|");
            } catch (Exception e) {
                System.err.println("Error solicitando usuarios: " + e.getMessage());
            }
        }
    }
    
    private void solicitarHistorial() {
        if (conectado && escritor != null) {
            try {
                escritor.println("GET_HISTORY|");
            } catch (Exception e) {
                System.err.println("Error solicitando historial: " + e.getMessage());
            }
        }
    }
    
    private void mostrarError(String mensaje) {
        JOptionPane.showMessageDialog(this, mensaje, "Error", JOptionPane.ERROR_MESSAGE);
    }
    
    private void cerrarAplicacion() {
        conectado = false;
        
        // Cerrar ventana de notificación si existe
        if (ventanaNotificacion != null) {
            ventanaNotificacion.dispose();
        }
        
        // Cerrar conexiones
        try {
            if (escritor != null) {
                escritor.close();
            }
            if (lector != null) {
                lector.close();
            }
            if (socketCliente != null) {
                socketCliente.close();
            }
        } catch (Exception e) {
            System.err.println("Error cerrando conexión: " + e.getMessage());
        }
        
        System.exit(0);
    }
    
    public static void main(String[] args) {
        // Configurar look and feel del sistema
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            System.err.println("Error configurando look and feel: " + e.getMessage());
        }
        
        // Crear y mostrar la aplicación
        SwingUtilities.invokeLater(() -> {
            new ClienteChat();
        });
    }
}