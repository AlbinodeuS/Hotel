import customtkinter as ctk
import sqlite3
from tkinter import ttk, messagebox
from werkzeug.security import check_password_hash, generate_password_hash

# --- CONFIGURACIÓN DE APARIENCIA ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# --- CLASE PARA LA VENTANA DE LOGIN ---
class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Login - HotelPy")
        self.geometry("350x220")
        self.parent = parent
        self.protocol("WM_DELETE_WINDOW", self.parent.destroy)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Inicio de Sesión", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Usuario")
        self.username_entry.grid(row=1, column=0, pady=5, padx=20, sticky="ew")
        
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*")
        self.password_entry.grid(row=2, column=0, pady=5, padx=20, sticky="ew")
        
        login_button = ctk.CTkButton(self, text="Iniciar Sesión", command=self.attempt_login)
        login_button.grid(row=3, column=0, pady=(15, 20), padx=20, sticky="ew")

        self.transient(self.parent)
        self.grab_set()

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Usuario y contraseña no pueden estar vacíos.")
            return

        conn = sqlite3.connect('hotel.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM usuarios WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            self.parent.after(100, self.parent.deiconify)
            self.destroy()
        else:
            messagebox.showerror("Error de Login", "Usuario o contraseña incorrectos.")


# --- CLASE PRINCIPAL DE LA APLICACIÓN ---
class HotelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Hotel")
        self.geometry("1200x800")

        self.current_building_id = None
        self.current_view = "personal"
        self.personal_map = {}; self.building_map = {}
        self.selected_staff_id = None
        self.selected_client_id = None
        self.selected_room_id = None
        self.selected_building_id_mgmt = None
        self.selected_reservation_id = None # ID de la reserva seleccionada
        self.client_map = {} # Mapa de clientes para los menús
        self.available_rooms_map = {} # Mapa de habitaciones disponibles
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.setup_top_frame()
        self.setup_nav_frame()

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 20))
        
        self.update_building_selector()

    def setup_top_frame(self):
        self.top_frame = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color=("#dbdbdb", "#2B2B2B"))
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        ctk.CTkLabel(self.top_frame, text="Edificio Actual:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(20, 10), pady=10)
        
        self.building_selector = ctk.CTkOptionMenu(self.top_frame, values=[""], command=self.on_building_change)
        self.building_selector.pack(side="left", padx=10, pady=10)

    def setup_nav_frame(self):
        nav_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        nav_frame.grid(row=1, column=0, sticky="nsew")
        nav_frame.grid_rowconfigure(7, weight=1) # Aumentar el peso de la fila
        ctk.CTkLabel(nav_frame, text="HotelPy", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20)
        self.btn_personal = ctk.CTkButton(nav_frame, text="Personal", command=self.mostrar_vista_personal)
        self.btn_personal.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.btn_habitaciones = ctk.CTkButton(nav_frame, text="Habitaciones", command=self.mostrar_vista_habitaciones)
        self.btn_habitaciones.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # --- NUEVO BOTÓN DE CLIENTES ---
        self.btn_clientes = ctk.CTkButton(nav_frame, text="Clientes", command=self.mostrar_vista_clientes)
        self.btn_clientes.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        # --- BOTON RESERVAS ---
        self.btn_reservas = ctk.CTkButton(nav_frame, text="Reservas", command=self.mostrar_vista_reservas)
        self.btn_reservas.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(nav_frame, text="Administración", font=ctk.CTkFont(size=12, weight="bold", slant="italic")).grid(row=4, column=0, padx=20, pady=(20, 0), sticky="w")
        self.btn_edificios = ctk.CTkButton(nav_frame, text="Edificios", fg_color="#565b5e", hover_color="#6c7174", command=self.mostrar_vista_edificios)
        self.btn_edificios.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

    def db_connect(self): return sqlite3.connect('hotel.db')

    def limpiar_frame_principal(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

    def update_building_selector(self):
        edificios = list(self.get_all_buildings_for_map().keys())
        if not edificios: edificios = ["Sin edificios"]
        current_selection = self.building_selector.get()
        self.building_selector.configure(values=edificios)
        if current_selection in edificios:
            self.building_selector.set(current_selection)
            self.on_building_change(current_selection)
        elif edificios[0] != "Sin edificios":
            self.building_selector.set(edificios[0])
            self.on_building_change(edificios[0])
        else:
            self.building_selector.set("Sin edificios")
            self.current_building_id = None
            if self.current_view != "edificios":
                self.mostrar_vista_vacia("No hay edificios. Agregue uno para empezar.")
            
    def get_all_buildings_for_map(self):
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM edificios ORDER BY nombre")
        building_list = cursor.fetchall()
        conn.close()
        self.building_map = {name: id for id, name in building_list}
        return self.building_map

    def get_staff_for_building_map(self, building_id):
        if not building_id: return []
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_completo FROM personal WHERE id_edificio = ?", (building_id,))
        staff_list = cursor.fetchall()
        conn.close()
        self.personal_map = {name: id for id, name in staff_list}
        return [name for id, name in staff_list]
        
    def on_building_change(self, building_name):
        self.current_building_id = self.building_map.get(building_name)
        if self.current_view == "personal": self.mostrar_vista_personal()
        elif self.current_view == "habitaciones": self.mostrar_vista_habitaciones()
        elif self.current_view == "reservas": self.mostrar_vista_reservas()

    def mostrar_vista_vacia(self, message):
        self.limpiar_frame_principal()
        ctk.CTkLabel(self.main_frame, text=message, font=ctk.CTkFont(size=18)).pack(expand=True, padx=20, pady=20)

    def mostrar_vista_personal(self):
        self.current_view = "personal"; self.top_frame.grid()
        self.limpiar_frame_principal()
        if not self.current_building_id: self.mostrar_vista_vacia("Seleccione un edificio para ver al personal."); return
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent"); container.pack(fill="both", expand=True)
        self.setup_personal_view(container)

    def mostrar_vista_habitaciones(self):
        self.current_view = "habitaciones"; self.top_frame.grid()
        self.limpiar_frame_principal()
        if not self.current_building_id: self.mostrar_vista_vacia("Seleccione un edificio para ver las habitaciones."); return
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent"); container.pack(fill="both", expand=True)
        self.setup_habitaciones_view(container)
        
    def mostrar_vista_edificios(self):
        self.current_view = "edificios"; self.top_frame.grid_remove()
        self.limpiar_frame_principal()
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent"); container.pack(fill="both", expand=True)
        self.setup_edificios_view(container)
        
    # --- NUEVA VISTA DE CLIENTES ---
    def mostrar_vista_clientes(self):
        self.current_view = "clientes"
        self.top_frame.grid_remove()  # Oculta el selector de edificios
        self.limpiar_frame_principal()
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)
        self.setup_clientes_view(container)

    # --- VISTA Y LÓGICA DE GESTIÓN DE CLIENTES ---
    def setup_clientes_view(self, parent_container):
        parent_container.grid_columnconfigure(0, weight=1); parent_container.grid_rowconfigure(1, weight=3); parent_container.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(parent_container, text="Gestión de Clientes", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=10, pady=(10,15), sticky="w")
        
        # Tabla de Clientes
        tabla_frame = ctk.CTkFrame(parent_container); tabla_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        tabla_frame.grid_columnconfigure(0, weight=1); tabla_frame.grid_rowconfigure(0, weight=1)
        self.tree_clientes = ttk.Treeview(tabla_frame, columns=("ID", "Nombre", "RUT", "Email", "Teléfono"), show="headings")
        self.tree_clientes.heading("ID", text="ID"); self.tree_clientes.column("ID", width=50, anchor="center")
        self.tree_clientes.heading("Nombre", text="Nombre Completo"); self.tree_clientes.column("Nombre", width=250)
        self.tree_clientes.heading("RUT", text="RUT/Documento"); self.tree_clientes.column("RUT", width=150)
        self.tree_clientes.heading("Email", text="Email"); self.tree_clientes.column("Email", width=200)
        self.tree_clientes.heading("Teléfono", text="Teléfono"); self.tree_clientes.column("Teléfono", width=120)
        self.tree_clientes.pack(fill="both", expand=True)
        self.refrescar_tabla_clientes()
        self.tree_clientes.bind("<<TreeviewSelect>>", self.on_cliente_select)
        
        # Paneles de Acciones
        acciones_frame = ctk.CTkFrame(parent_container, fg_color="transparent"); acciones_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        acciones_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Panel Agregar Cliente
        agregar_frame = ctk.CTkFrame(acciones_frame, border_width=1); agregar_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        agregar_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(agregar_frame, text="Agregar Nuevo Cliente", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(5,10))
        self.add_nombre_cliente = ctk.CTkEntry(agregar_frame, placeholder_text="Nombre Completo"); self.add_nombre_cliente.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.add_rut_cliente = ctk.CTkEntry(agregar_frame, placeholder_text="RUT/Documento"); self.add_rut_cliente.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.add_email_cliente = ctk.CTkEntry(agregar_frame, placeholder_text="Email"); self.add_email_cliente.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        self.add_telefono_cliente = ctk.CTkEntry(agregar_frame, placeholder_text="Teléfono"); self.add_telefono_cliente.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(agregar_frame, text="Agregar Cliente", command=self.agregar_cliente).grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        # Panel Editar/Eliminar Cliente
        self.edit_frame_cliente = ctk.CTkFrame(acciones_frame, border_width=1); self.edit_frame_cliente.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self.edit_frame_cliente.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkLabel(self.edit_frame_cliente, text="Editar Cliente Seleccionado", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(5,10))
        self.edit_nombre_cliente = ctk.CTkEntry(self.edit_frame_cliente); self.edit_nombre_cliente.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.edit_rut_cliente = ctk.CTkEntry(self.edit_frame_cliente); self.edit_rut_cliente.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.edit_email_cliente = ctk.CTkEntry(self.edit_frame_cliente); self.edit_email_cliente.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.edit_telefono_cliente = ctk.CTkEntry(self.edit_frame_cliente); self.edit_telefono_cliente.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.edit_frame_cliente, text="Actualizar", command=self.actualizar_cliente).grid(row=5, column=0, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(self.edit_frame_cliente, text="Eliminar", fg_color="red", hover_color="#C00000", command=self.eliminar_cliente).grid(row=5, column=1, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(self.edit_frame_cliente, text="Limpiar", fg_color="gray", command=self.limpiar_seleccion_cliente).grid(row=5, column=2, padx=5, pady=10, sticky="ew")
        self.toggle_edit_panel_cliente(False)

    def refrescar_tabla_clientes(self):
        for item in self.tree_clientes.get_children(): self.tree_clientes.delete(item)
        conn = self.db_connect(); cursor = conn.cursor()
        for row in cursor.execute("SELECT id, nombre_completo, rut_documento, email, telefono FROM clientes ORDER BY nombre_completo"):
            self.tree_clientes.insert("", "end", values=row)
        conn.close()

    def on_cliente_select(self, event):
        selected_item = self.tree_clientes.focus()
        if not selected_item: return
        item_values = self.tree_clientes.item(selected_item, "values")
        self.selected_client_id = item_values[0]
        
        self.edit_nombre_cliente.delete(0, "end"); self.edit_nombre_cliente.insert(0, item_values[1])
        self.edit_rut_cliente.delete(0, "end"); self.edit_rut_cliente.insert(0, item_values[2])
        self.edit_email_cliente.delete(0, "end"); self.edit_email_cliente.insert(0, item_values[3])
        self.edit_telefono_cliente.delete(0, "end"); self.edit_telefono_cliente.insert(0, item_values[4] if item_values[4] else "")
        self.toggle_edit_panel_cliente(True)

    def agregar_cliente(self):
        nombre = self.add_nombre_cliente.get()
        rut = self.add_rut_cliente.get()
        email = self.add_email_cliente.get()
        telefono = self.add_telefono_cliente.get()

        if not nombre or not rut:
            messagebox.showwarning("Campos Vacíos", "El nombre y el RUT son obligatorios.")
            return

        try:
            conn = self.db_connect(); cursor = conn.cursor()
            cursor.execute("INSERT INTO clientes (nombre_completo, rut_documento, email, telefono) VALUES (?, ?, ?, ?)", (nombre, rut, email, telefono))
            conn.commit(); conn.close()
            
            # Limpiar campos de entrada
            self.add_nombre_cliente.delete(0, "end")
            self.add_rut_cliente.delete(0, "end")
            self.add_email_cliente.delete(0, "end")
            self.add_telefono_cliente.delete(0, "end")
            
            self.refrescar_tabla_clientes()
            messagebox.showinfo("Éxito", "Cliente agregado correctamente.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe un cliente con ese RUT/Documento.")

    def actualizar_cliente(self):
        if not self.selected_client_id: return

        nombre = self.edit_nombre_cliente.get()
        rut = self.edit_rut_cliente.get()
        email = self.edit_email_cliente.get()
        telefono = self.edit_telefono_cliente.get()

        if not nombre or not rut:
            messagebox.showwarning("Campos Vacíos", "El nombre y el RUT son obligatorios.")
            return

        try:
            conn = self.db_connect(); cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET nombre_completo = ?, rut_documento = ?, email = ?, telefono = ? WHERE id = ?", (nombre, rut, email, telefono, self.selected_client_id))
            conn.commit(); conn.close()
            self.refrescar_tabla_clientes()
            self.limpiar_seleccion_cliente()
            messagebox.showinfo("Éxito", "Cliente actualizado correctamente.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe otro cliente con ese RUT/Documento.")

    def eliminar_cliente(self):
        if not self.selected_client_id: return
        
        # Verificar si el cliente tiene reservas
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reservas WHERE id_cliente = ?", (self.selected_client_id,))
        reservas_count = cursor.fetchone()[0]
        
        if reservas_count > 0:
            messagebox.showerror("Error al Eliminar", f"No se puede eliminar el cliente.\nTiene {reservas_count} reserva(s) asociada(s).\nPor favor, gestione las reservas primero.")
            conn.close()
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Seguro que desea eliminar al cliente '{self.edit_nombre_cliente.get()}'? Esta acción no se puede deshacer."):
            cursor.execute("DELETE FROM clientes WHERE id = ?", (self.selected_client_id,))
            conn.commit(); conn.close()
            self.refrescar_tabla_clientes()
            self.limpiar_seleccion_cliente()
            messagebox.showinfo("Éxito", "Cliente eliminado.")

    def limpiar_seleccion_cliente(self):
        if self.tree_clientes.focus(): self.tree_clientes.selection_remove(self.tree_clientes.focus())
        self.selected_client_id = None
        self.edit_nombre_cliente.delete(0, "end"); self.edit_rut_cliente.delete(0, "end"); self.edit_email_cliente.delete(0, "end"); self.edit_telefono_cliente.delete(0, "end")
        self.edit_nombre_cliente.configure(placeholder_text="Seleccione un cliente de la lista")
        self.toggle_edit_panel_cliente(False)

    def toggle_edit_panel_cliente(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.edit_frame_cliente.winfo_children():
            if isinstance(child, (ctk.CTkEntry, ctk.CTkButton)):
                child.configure(state=state)
    # --- VISTA Y LÓGICA DE GESTIÓN DE RESERVAS ---
    def mostrar_vista_reservas(self):
        self.current_view = "reservas"; self.top_frame.grid()
        self.limpiar_frame_principal()
        if not self.current_building_id: self.mostrar_vista_vacia("Seleccione un edificio para gestionar las reservas."); return
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent"); container.pack(fill="both", expand=True)
        self.setup_reservas_view(container)

    def setup_reservas_view(self, parent_container):
        parent_container.grid_columnconfigure(0, weight=2); parent_container.grid_columnconfigure(1, weight=1); 
        parent_container.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(parent_container, text=f"Gestión de Reservas - {self.building_selector.get()}", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10,15), sticky="w")
        
        # Panel Izquierdo: Tabla de Reservas
        tabla_frame = ctk.CTkFrame(parent_container); tabla_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5))
        tabla_frame.grid_columnconfigure(0, weight=1); tabla_frame.grid_rowconfigure(0, weight=1)
        self.tree_reservas = ttk.Treeview(tabla_frame, columns=("ID", "Cliente", "Habitación", "Check-in", "Check-out"), show="headings")
        self.tree_reservas.heading("ID", text="ID"); self.tree_reservas.column("ID", width=40, anchor="center")
        self.tree_reservas.heading("Cliente", text="Cliente"); self.tree_reservas.column("Cliente", width=200)
        self.tree_reservas.heading("Habitación", text="Habitación"); self.tree_reservas.column("Habitación", width=100, anchor="center")
        self.tree_reservas.heading("Check-in", text="Check-in"); self.tree_reservas.column("Check-in", width=120, anchor="center")
        self.tree_reservas.heading("Check-out", text="Check-out"); self.tree_reservas.column("Check-out", width=120, anchor="center")
        self.tree_reservas.pack(fill="both", expand=True)
        self.refrescar_tabla_reservas()
        self.tree_reservas.bind("<<TreeviewSelect>>", self.on_reserva_select)
        
        # Panel Derecho: Acciones
        acciones_frame = ctk.CTkFrame(parent_container, fg_color="transparent"); acciones_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10))
        acciones_frame.grid_rowconfigure(1, weight=1)

        # Formulario para Crear Reserva
        crear_reserva_frame = ctk.CTkFrame(acciones_frame, border_width=1); crear_reserva_frame.grid(row=0, column=0, sticky="ew")
        crear_reserva_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(crear_reserva_frame, text="Crear Nueva Reserva", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(10,5))
        
        ctk.CTkLabel(crear_reserva_frame, text="Cliente:").grid(row=1, column=0, padx=10, pady=(5,0), sticky="w")
        self.reserva_cliente_selector = ctk.CTkOptionMenu(crear_reserva_frame, values=["Cargando..."]); self.reserva_cliente_selector.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(crear_reserva_frame, text="Habitación Disponible:").grid(row=3, column=0, padx=10, pady=(5,0), sticky="w")
        self.reserva_habitacion_selector = ctk.CTkOptionMenu(crear_reserva_frame, values=["Cargando..."]); self.reserva_habitacion_selector.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(crear_reserva_frame, text="Fecha Check-in (AAAA-MM-DD):").grid(row=5, column=0, padx=10, pady=(5,0), sticky="w")
        self.reserva_checkin_entry = ctk.CTkEntry(crear_reserva_frame); self.reserva_checkin_entry.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(crear_reserva_frame, text="Fecha Check-out (AAAA-MM-DD):").grid(row=7, column=0, padx=10, pady=(5,0), sticky="w")
        self.reserva_checkout_entry = ctk.CTkEntry(crear_reserva_frame); self.reserva_checkout_entry.grid(row=8, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkButton(crear_reserva_frame, text="Confirmar Reserva", command=self.crear_reserva).grid(row=9, column=0, padx=10, pady=10, sticky="ew")

        # Panel para Cancelar Reserva
        self.cancelar_reserva_frame = ctk.CTkFrame(acciones_frame, border_width=1); self.cancelar_reserva_frame.grid(row=1, column=0, sticky="sew", pady=(10,0))
        self.cancelar_reserva_frame.grid_columnconfigure(0, weight=1)
        self.label_cancelar = ctk.CTkLabel(self.cancelar_reserva_frame, text="Seleccione una reserva para cancelarla", wraplength=250)
        self.label_cancelar.grid(row=0, column=0, padx=10, pady=10)
        self.btn_cancelar_reserva = ctk.CTkButton(self.cancelar_reserva_frame, text="Cancelar Reserva Seleccionada", fg_color="red", hover_color="#C00000", command=self.cancelar_reserva, state="disabled")
        self.btn_cancelar_reserva.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.actualizar_selectores_reserva()

    def refrescar_tabla_reservas(self):
        for item in self.tree_reservas.get_children(): self.tree_reservas.delete(item)
        conn = self.db_connect(); cursor = conn.cursor()
        query = """
            SELECT r.id, c.nombre_completo, h.numero_habitacion, r.fecha_check_in, r.fecha_check_out
            FROM reservas r
            JOIN clientes c ON r.id_cliente = c.id
            JOIN habitaciones h ON r.id_habitacion = h.id
            WHERE h.id_edificio = ?
            ORDER BY r.fecha_check_in DESC
        """
        for row in cursor.execute(query, (self.current_building_id,)):
            self.tree_reservas.insert("", "end", values=row)
        conn.close()

    def actualizar_selectores_reserva(self):
        # Actualizar clientes
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("SELECT id, nombre_completo FROM clientes ORDER BY nombre_completo")
        clientes = cursor.fetchall()
        self.client_map = {nombre: id for id, nombre in clientes}
        lista_clientes = list(self.client_map.keys()) if self.client_map else ["No hay clientes"]
        self.reserva_cliente_selector.configure(values=lista_clientes)
        if lista_clientes[0] != "No hay clientes": self.reserva_cliente_selector.set(lista_clientes[0])

        # Actualizar habitaciones disponibles
        cursor.execute("SELECT id, numero_habitacion FROM habitaciones WHERE id_edificio = ? AND estado = 'Disponible' ORDER BY numero_habitacion", (self.current_building_id,))
        habitaciones = cursor.fetchall()
        self.available_rooms_map = {f"Hab. {num}": id for id, num in habitaciones}
        lista_habitaciones = list(self.available_rooms_map.keys()) if self.available_rooms_map else ["No hay habitaciones disp."]
        self.reserva_habitacion_selector.configure(values=lista_habitaciones)
        if lista_habitaciones[0] != "No hay habitaciones disp.": self.reserva_habitacion_selector.set(lista_habitaciones[0])
        conn.close()

    def on_reserva_select(self, event):
        selected_item = self.tree_reservas.focus()
        if not selected_item: 
            self.selected_reservation_id = None
            self.btn_cancelar_reserva.configure(state="disabled")
            return
        item_values = self.tree_reservas.item(selected_item, "values")
        self.selected_reservation_id = item_values[0]
        self.label_cancelar.configure(text=f"Cancelar reserva de:\n{item_values[1]}\nHabitación: {item_values[2]}")
        self.btn_cancelar_reserva.configure(state="normal")
    
    def crear_reserva(self):
        cliente_nombre = self.reserva_cliente_selector.get()
        habitacion_nombre = self.reserva_habitacion_selector.get()
        check_in = self.reserva_checkin_entry.get()
        check_out = self.reserva_checkout_entry.get()

        if cliente_nombre == "No hay clientes" or habitacion_nombre == "No hay habitaciones disp.":
            messagebox.showerror("Error", "Debe haber clientes y habitaciones disponibles para crear una reserva.")
            return
        
        if not check_in or not check_out:
            messagebox.showwarning("Campos incompletos", "Las fechas de Check-in y Check-out son obligatorias.")
            return

        cliente_id = self.client_map.get(cliente_nombre)
        habitacion_id = self.available_rooms_map.get(habitacion_nombre)
        
        conn = self.db_connect(); cursor = conn.cursor()
        try:
            # Insertar la nueva reserva
            cursor.execute("INSERT INTO reservas (id_cliente, id_habitacion, fecha_check_in, fecha_check_out) VALUES (?, ?, ?, ?)",
                           (cliente_id, habitacion_id, check_in, check_out))
            
            # Actualizar el estado de la habitación
            cursor.execute("UPDATE habitaciones SET estado = 'Ocupada', fecha_disponible = ? WHERE id = ?", (check_out, habitacion_id))
            
            conn.commit()
            messagebox.showinfo("Éxito", "Reserva creada correctamente.")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error de base de datos", f"No se pudo crear la reserva: {e}")
        finally:
            conn.close()

        # Limpiar campos y refrescar vistas
        self.reserva_checkin_entry.delete(0, "end")
        self.reserva_checkout_entry.delete(0, "end")
        self.refrescar_tabla_reservas()
        self.actualizar_selectores_reserva() # Para quitar la habitación de la lista de disponibles

    def cancelar_reserva(self):
        if not self.selected_reservation_id: return

        if not messagebox.askyesno("Confirmar Cancelación", "¿Está seguro de que desea cancelar esta reserva? Esta acción cambiará el estado de la habitación a 'Disponible'."):
            return

        conn = self.db_connect(); cursor = conn.cursor()
        try:
            # Obtener el ID de la habitación antes de borrar la reserva
            cursor.execute("SELECT id_habitacion FROM reservas WHERE id = ?", (self.selected_reservation_id,))
            result = cursor.fetchone()
            if not result:
                messagebox.showerror("Error", "No se encontró la reserva.")
                return
            habitacion_id = result[0]
            
            # Eliminar la reserva
            cursor.execute("DELETE FROM reservas WHERE id = ?", (self.selected_reservation_id,))
            
            # Actualizar la habitación a 'Disponible'
            cursor.execute("UPDATE habitaciones SET estado = 'Disponible', fecha_disponible = NULL WHERE id = ?", (habitacion_id,))
            
            conn.commit()
            messagebox.showinfo("Éxito", "La reserva ha sido cancelada.")
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Error de base de datos", f"No se pudo cancelar la reserva: {e}")
        finally:
            conn.close()
        
        self.selected_reservation_id = None
        self.btn_cancelar_reserva.configure(state="disabled")
        self.label_cancelar.configure(text="Seleccione una reserva para cancelarla")
        self.refrescar_tabla_reservas()
        self.actualizar_selectores_reserva() # La habitación volverá a estar disponible

    # --- VISTA Y LÓGICA DE GESTIÓN DE EDIFICIOS ---
    def setup_edificios_view(self, parent_container):
        parent_container.grid_columnconfigure(0, weight=1); parent_container.grid_rowconfigure(1, weight=3); parent_container.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(parent_container, text="Gestión de Edificios", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=10, pady=(10,15), sticky="w")
        
        # Tabla
        tabla_frame = ctk.CTkFrame(parent_container); tabla_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        tabla_frame.grid_columnconfigure(0, weight=1); tabla_frame.grid_rowconfigure(0, weight=1)
        self.tree_edificios = ttk.Treeview(tabla_frame, columns=("ID", "Nombre", "Direccion"), show="headings")
        self.tree_edificios.heading("ID", text="ID"); self.tree_edificios.column("ID", width=50, anchor="center")
        self.tree_edificios.heading("Nombre", text="Nombre del Edificio"); self.tree_edificios.column("Nombre", width=300)
        self.tree_edificios.heading("Direccion", text="Dirección"); self.tree_edificios.column("Direccion", width=400)
        self.tree_edificios.pack(fill="both", expand=True)
        self.refrescar_tabla_edificios()
        self.tree_edificios.bind("<<TreeviewSelect>>", self.on_edificio_select)
        
        # Paneles de Acciones
        acciones_frame = ctk.CTkFrame(parent_container, fg_color="transparent"); acciones_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        acciones_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Panel Agregar
        agregar_frame = ctk.CTkFrame(acciones_frame, border_width=1); agregar_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        agregar_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(agregar_frame, text="Agregar Nuevo Edificio", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(5,10))
        self.add_nombre_edificio = ctk.CTkEntry(agregar_frame, placeholder_text="Nombre del Edificio"); self.add_nombre_edificio.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.add_direccion_edificio = ctk.CTkEntry(agregar_frame, placeholder_text="Dirección"); self.add_direccion_edificio.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(agregar_frame, text="Agregar Edificio", command=self.agregar_edificio).grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # Panel Editar/Eliminar
        self.edit_frame_edificio = ctk.CTkFrame(acciones_frame, border_width=1); self.edit_frame_edificio.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self.edit_frame_edificio.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkLabel(self.edit_frame_edificio, text="Editar Edificio Seleccionado", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(5,10))
        self.edit_nombre_edificio = ctk.CTkEntry(self.edit_frame_edificio); self.edit_nombre_edificio.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.edit_direccion_edificio = ctk.CTkEntry(self.edit_frame_edificio); self.edit_direccion_edificio.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.edit_frame_edificio, text="Actualizar", command=self.actualizar_edificio).grid(row=3, column=0, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(self.edit_frame_edificio, text="Eliminar", fg_color="red", hover_color="#C00000", command=self.eliminar_edificio).grid(row=3, column=1, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(self.edit_frame_edificio, text="Limpiar", fg_color="gray", command=self.limpiar_seleccion_edificio).grid(row=3, column=2, padx=5, pady=10, sticky="ew")
        self.toggle_edit_panel_edificio(False)

    def refrescar_tabla_edificios(self):
        for item in self.tree_edificios.get_children(): self.tree_edificios.delete(item)
        conn = self.db_connect(); cursor = conn.cursor()
        for row in cursor.execute("SELECT id, nombre, direccion FROM edificios"): self.tree_edificios.insert("", "end", values=row)
        conn.close()

    def on_edificio_select(self, event):
        selected_item = self.tree_edificios.focus()
        if not selected_item: return
        item_values = self.tree_edificios.item(selected_item, "values"); self.selected_building_id_mgmt = item_values[0]
        self.edit_nombre_edificio.delete(0, "end"); self.edit_nombre_edificio.insert(0, item_values[1])
        self.edit_direccion_edificio.delete(0, "end"); self.edit_direccion_edificio.insert(0, item_values[2])
        self.toggle_edit_panel_edificio(True)

    def agregar_edificio(self):
        nombre = self.add_nombre_edificio.get(); direccion = self.add_direccion_edificio.get()
        if nombre and direccion:
            try:
                conn = self.db_connect(); cursor = conn.cursor()
                cursor.execute("INSERT INTO edificios (nombre, direccion) VALUES (?, ?)", (nombre, direccion))
                conn.commit(); conn.close()
                self.add_nombre_edificio.delete(0, "end"); self.add_direccion_edificio.delete(0, "end")
                self.refrescar_tabla_edificios(); self.update_building_selector()
            except sqlite3.IntegrityError: messagebox.showerror("Error", "Ya existe un edificio con ese nombre.")
        else: messagebox.showwarning("Campos Vacíos", "El nombre y la dirección son obligatorios.")

    def actualizar_edificio(self):
        if not self.selected_building_id_mgmt: return
        nombre = self.edit_nombre_edificio.get(); direccion = self.edit_direccion_edificio.get()
        if nombre and direccion:
            conn = self.db_connect(); cursor = conn.cursor()
            cursor.execute("UPDATE edificios SET nombre = ?, direccion = ? WHERE id = ?", (nombre, direccion, self.selected_building_id_mgmt))
            conn.commit(); conn.close()
            self.refrescar_tabla_edificios(); self.limpiar_seleccion_edificio(); self.update_building_selector()
        else: messagebox.showwarning("Campos Vacíos", "El nombre y la dirección son obligatorios.")

    def eliminar_edificio(self):
        if not self.selected_building_id_mgmt: return
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM personal WHERE id_edificio = ?", (self.selected_building_id_mgmt,))
        staff_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM habitaciones WHERE id_edificio = ?", (self.selected_building_id_mgmt,))
        room_count = cursor.fetchone()[0]
        
        if staff_count > 0 or room_count > 0:
            messagebox.showerror("Error al Eliminar", f"No se puede eliminar el edificio.\nTiene {staff_count} trabajador(es) y {room_count} habitación(es) asignadas.\nPor favor, reasígnelos o elimínelos primero.")
            conn.close()
            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Seguro que desea eliminar el edificio '{self.edit_nombre_edificio.get()}'?"):
            cursor.execute("DELETE FROM edificios WHERE id = ?", (self.selected_building_id_mgmt,))
            conn.commit(); conn.close()
            self.refrescar_tabla_edificios(); self.limpiar_seleccion_edificio(); self.update_building_selector()

    def limpiar_seleccion_edificio(self):
        if self.tree_edificios.focus(): self.tree_edificios.selection_remove(self.tree_edificios.focus())
        self.selected_building_id_mgmt = None
        self.edit_nombre_edificio.delete(0, "end"); self.edit_direccion_edificio.delete(0, "end")
        self.edit_nombre_edificio.configure(placeholder_text="Seleccione un edificio"); self.edit_direccion_edificio.configure(placeholder_text="")
        self.toggle_edit_panel_edificio(False)

    def toggle_edit_panel_edificio(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.edit_frame_edificio.winfo_children():
            if isinstance(child, (ctk.CTkEntry, ctk.CTkButton)): child.configure(state=state)

    # --- VISTA Y LÓGICA DE PERSONAL ---
    def setup_personal_view(self, parent_container):
        parent_container.grid_columnconfigure(0, weight=1); parent_container.grid_rowconfigure(1, weight=3); parent_container.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(parent_container, text="Gestión de Personal", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=10, pady=(10,15), sticky="w")
        tabla_frame = ctk.CTkFrame(parent_container); tabla_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        tabla_frame.grid_columnconfigure(0, weight=1); tabla_frame.grid_rowconfigure(0, weight=1)
        self.tree_personal = ttk.Treeview(tabla_frame, columns=("ID", "Nombre", "Puesto", "Teléfono"), show="headings")
        self.tree_personal.heading("ID", text="ID"); self.tree_personal.column("ID", width=50, anchor="center")
        self.tree_personal.heading("Nombre", text="Nombre Completo"); self.tree_personal.column("Nombre", width=300)
        self.tree_personal.heading("Puesto", text="Puesto"); self.tree_personal.column("Puesto", width=200)
        self.tree_personal.heading("Teléfono", text="Teléfono"); self.tree_personal.column("Teléfono", width=150)
        self.tree_personal.pack(fill="both", expand=True)
        self.refrescar_tabla_personal()
        self.tree_personal.bind("<<TreeviewSelect>>", self.on_staff_select)
        acciones_frame = ctk.CTkFrame(parent_container, fg_color="transparent"); acciones_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        acciones_frame.grid_columnconfigure((0, 1), weight=1)
        agregar_frame = ctk.CTkFrame(acciones_frame, border_width=1); agregar_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        agregar_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(agregar_frame, text="Agregar Nuevo Trabajador", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(5,10))
        self.add_nombre_staff = ctk.CTkEntry(agregar_frame, placeholder_text="Nombre Completo"); self.add_nombre_staff.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.add_puesto_staff = ctk.CTkEntry(agregar_frame, placeholder_text="Puesto"); self.add_puesto_staff.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.add_telefono_staff = ctk.CTkEntry(agregar_frame, placeholder_text="Teléfono"); self.add_telefono_staff.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(agregar_frame, text="Agregar Trabajador", command=self.agregar_personal).grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        self.edit_frame_staff = ctk.CTkFrame(acciones_frame, border_width=1); self.edit_frame_staff.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self.edit_frame_staff.grid_columnconfigure((0,1,2), weight=1)
        ctk.CTkLabel(self.edit_frame_staff, text="Editar Trabajador Seleccionado", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(5,10))
        self.edit_nombre_staff = ctk.CTkEntry(self.edit_frame_staff, placeholder_text="Seleccione a alguien de la lista"); self.edit_nombre_staff.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.edit_puesto_staff = ctk.CTkEntry(self.edit_frame_staff); self.edit_puesto_staff.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        self.edit_telefono_staff = ctk.CTkEntry(self.edit_frame_staff); self.edit_telefono_staff.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.edit_frame_staff, text="Actualizar", command=self.actualizar_personal).grid(row=4, column=0, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(self.edit_frame_staff, text="Eliminar", fg_color="red", hover_color="#C00000", command=self.eliminar_personal).grid(row=4, column=1, padx=5, pady=10, sticky="ew")
        ctk.CTkButton(self.edit_frame_staff, text="Limpiar", fg_color="gray", command=self.limpiar_seleccion_personal).grid(row=4, column=2, padx=5, pady=10, sticky="ew")
        self.toggle_edit_panel_staff(False)

    def refrescar_tabla_personal(self):
        for item in self.tree_personal.get_children(): self.tree_personal.delete(item)
        if not self.current_building_id: return
        conn = self.db_connect(); cursor = conn.cursor()
        for row in cursor.execute("SELECT id, nombre_completo, puesto, telefono FROM personal WHERE id_edificio = ?", (self.current_building_id,)):
            self.tree_personal.insert("", "end", values=row)
        conn.close()

    def on_staff_select(self, event):
        selected_item = self.tree_personal.focus()
        if not selected_item: return
        item_values = self.tree_personal.item(selected_item, "values"); self.selected_staff_id = item_values[0]
        self.edit_nombre_staff.delete(0, "end"); self.edit_nombre_staff.insert(0, item_values[1])
        self.edit_puesto_staff.delete(0, "end"); self.edit_puesto_staff.insert(0, item_values[2])
        self.edit_telefono_staff.delete(0, "end"); self.edit_telefono_staff.insert(0, item_values[3])
        self.toggle_edit_panel_staff(True)

    def agregar_personal(self):
        nombre = self.add_nombre_staff.get(); puesto = self.add_puesto_staff.get(); telefono = self.add_telefono_staff.get()
        if nombre and puesto:
            conn = self.db_connect(); cursor = conn.cursor()
            cursor.execute("INSERT INTO personal (id_edificio, nombre_completo, puesto, telefono) VALUES (?, ?, ?, ?)", (self.current_building_id, nombre, puesto, telefono))
            conn.commit(); conn.close()
            self.add_nombre_staff.delete(0, "end"); self.add_puesto_staff.delete(0, "end"); self.add_telefono_staff.delete(0, "end")
            self.refrescar_tabla_personal()
        else: messagebox.showwarning("Campos Vacíos", "El nombre y el puesto son obligatorios.")
    
    def actualizar_personal(self):
        if not self.selected_staff_id: return
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("UPDATE personal SET nombre_completo = ?, puesto = ?, telefono = ? WHERE id = ?", (self.edit_nombre_staff.get(), self.edit_puesto_staff.get(), self.edit_telefono_staff.get(), self.selected_staff_id))
        conn.commit(); conn.close()
        self.refrescar_tabla_personal(); self.limpiar_seleccion_personal()

    def eliminar_personal(self):
        if not self.selected_staff_id: return
        if messagebox.askyesno("Confirmar Eliminación", f"¿Seguro que desea eliminar a {self.edit_nombre_staff.get()}?"):
            conn = self.db_connect(); cursor = conn.cursor()
            cursor.execute("UPDATE habitaciones SET id_personal_asignado = NULL WHERE id_personal_asignado = ?", (self.selected_staff_id,))
            cursor.execute("DELETE FROM personal WHERE id = ?", (self.selected_staff_id,))
            conn.commit(); conn.close()
            self.refrescar_tabla_personal(); self.limpiar_seleccion_personal()

    def limpiar_seleccion_personal(self):
        if self.tree_personal.focus(): self.tree_personal.selection_remove(self.tree_personal.focus())
        self.selected_staff_id = None
        self.edit_nombre_staff.delete(0, "end"); self.edit_puesto_staff.delete(0, "end"); self.edit_telefono_staff.delete(0, "end")
        self.edit_nombre_staff.configure(placeholder_text="Seleccione a alguien de la lista")
        self.toggle_edit_panel_staff(False)

    def toggle_edit_panel_staff(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.edit_frame_staff.winfo_children():
            if isinstance(child, (ctk.CTkEntry, ctk.CTkButton)): child.configure(state=state)

    # --- VISTA Y LÓGICA DE HABITACIONES ---
    def setup_habitaciones_view(self, parent_container):
        parent_container.grid_columnconfigure(0, weight=1); parent_container.grid_rowconfigure(1, weight=3); parent_container.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(parent_container, text="Gestión de Habitaciones", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=10, pady=(10,15), sticky="w")
        tabla_frame = ctk.CTkFrame(parent_container); tabla_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        tabla_frame.grid_columnconfigure(0, weight=1); tabla_frame.grid_rowconfigure(0, weight=1)
        self.tree_habitaciones = ttk.Treeview(tabla_frame, columns=("ID", "Numero", "Tipo", "Estado", "Disponible", "Personal"), show="headings")
        self.tree_habitaciones.heading("ID", text="ID"); self.tree_habitaciones.column("ID", width=40, anchor="center")
        self.tree_habitaciones.heading("Numero", text="Número"); self.tree_habitaciones.column("Numero", width=80)
        self.tree_habitaciones.heading("Tipo", text="Tipo"); self.tree_habitaciones.column("Tipo", width=100)
        self.tree_habitaciones.heading("Estado", text="Estado"); self.tree_habitaciones.column("Estado", width=100)
        self.tree_habitaciones.heading("Disponible", text="Válido hasta"); self.tree_habitaciones.column("Disponible", width=150)
        self.tree_habitaciones.heading("Personal", text="Personal Asignado"); self.tree_habitaciones.column("Personal", width=200)
        self.tree_habitaciones.pack(fill="both", expand=True)
        self.refrescar_tabla_habitaciones()
        self.tree_habitaciones.bind("<<TreeviewSelect>>", self.on_room_select)
        acciones_frame = ctk.CTkFrame(parent_container, fg_color="transparent"); acciones_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        acciones_frame.grid_columnconfigure((0, 1), weight=1)
        agregar_frame = ctk.CTkFrame(acciones_frame, border_width=1); agregar_frame.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")
        agregar_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(agregar_frame, text="Agregar Nueva Habitación", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(5,10))
        self.add_numero_hab = ctk.CTkEntry(agregar_frame, placeholder_text="Número de Habitación"); self.add_numero_hab.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.add_tipo_hab = ctk.CTkOptionMenu(agregar_frame, values=["Individual", "Doble", "Suite", "Matrimonial"]); self.add_tipo_hab.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(agregar_frame, text="Agregar Habitación", command=self.agregar_habitacion).grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.edit_frame_room = ctk.CTkFrame(acciones_frame, border_width=1); self.edit_frame_room.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")
        self.edit_frame_room.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.edit_frame_room, text="Editar Habitación Seleccionada", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(5,10))
        self.edit_estado_hab = ctk.CTkOptionMenu(self.edit_frame_room, values=["Disponible", "Ocupada", "Mantenimiento"]); self.edit_estado_hab.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        staff_names = self.get_staff_for_building_map(self.current_building_id or 0); staff_names.insert(0, "Ninguno")
        self.edit_personal_hab = ctk.CTkOptionMenu(self.edit_frame_room, values=staff_names); self.edit_personal_hab.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(self.edit_frame_room, text="Actualizar Habitación", command=self.actualizar_habitacion).grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.toggle_edit_panel_room(False)

    def refrescar_tabla_habitaciones(self):
        for item in self.tree_habitaciones.get_children(): self.tree_habitaciones.delete(item)
        if not self.current_building_id: return
        conn = self.db_connect(); cursor = conn.cursor()
        query = """SELECT h.id, h.numero_habitacion, h.tipo, h.estado, h.fecha_disponible, p.nombre_completo FROM habitaciones h LEFT JOIN personal p ON h.id_personal_asignado = p.id WHERE h.id_edificio = ?"""
        for row in cursor.execute(query, (self.current_building_id,)):
            personal = row[5] if row[5] else "Sin asignar"; fecha = row[4] if row[4] else ""
            self.tree_habitaciones.insert("", "end", values=(row[0], row[1], row[2], row[3], fecha, personal))
        conn.close()

    def on_room_select(self, event):
        selected_item = self.tree_habitaciones.focus()
        if not selected_item: return
        item_values = self.tree_habitaciones.item(selected_item, "values"); self.selected_room_id = item_values[0]
        self.edit_estado_hab.set(item_values[3])
        staff_names = self.get_staff_for_building_map(self.current_building_id); staff_names.insert(0, "Ninguno")
        self.edit_personal_hab.configure(values=staff_names)
        self.edit_personal_hab.set(item_values[5] if item_values[5] != "Sin asignar" else "Ninguno")
        self.toggle_edit_panel_room(True)

    def agregar_habitacion(self):
        numero = self.add_numero_hab.get(); tipo = self.add_tipo_hab.get()
        if numero and tipo:
            conn = self.db_connect(); cursor = conn.cursor()
            cursor.execute("INSERT INTO habitaciones (id_edificio, numero_habitacion, tipo) VALUES (?, ?, ?)", (self.current_building_id, numero, tipo))
            conn.commit(); conn.close()
            self.add_numero_hab.delete(0, "end"); self.refrescar_tabla_habitaciones()
        else: messagebox.showwarning("Campos Vacíos", "El número y tipo son obligatorios.")

    def actualizar_habitacion(self):
        if not self.selected_room_id: return
        nuevo_estado = self.edit_estado_hab.get(); fecha_disp = None
        if nuevo_estado in ["Ocupada", "Mantenimiento"]:
            dialog = ctk.CTkInputDialog(text=f"¿Hasta qué fecha/hora estará '{nuevo_estado}'?\nFormato Sugerido: AAAA-MM-DD HH:MM", title="Confirmar Fecha")
            fecha_disp = dialog.get_input()
            if not fecha_disp: return
        personal_nombre = self.edit_personal_hab.get()
        personal_id = self.personal_map.get(personal_nombre) if personal_nombre != "Ninguno" else None
        params = (nuevo_estado, personal_id, fecha_disp if nuevo_estado != "Disponible" else None, self.selected_room_id)
        conn = self.db_connect(); cursor = conn.cursor()
        cursor.execute("UPDATE habitaciones SET estado = ?, id_personal_asignado = ?, fecha_disponible = ? WHERE id = ?", params)
        conn.commit(); conn.close()
        self.refrescar_tabla_habitaciones(); self.toggle_edit_panel_room(False); self.selected_room_id = None

    def toggle_edit_panel_room(self, enabled):
        state = "normal" if enabled else "disabled"
        for child in self.edit_frame_room.winfo_children():
            if isinstance(child, (ctk.CTkOptionMenu, ctk.CTkButton)): child.configure(state=state)

# --- PUNTO DE ENTRADA DE LA APLICACIÓN ---
if __name__ == "__main__":
    app = HotelApp()
    app.withdraw()
    login_window = LoginWindow(app)
    app.mainloop()
