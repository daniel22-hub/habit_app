import flet as ft
import json

# --- 1. Definimos las clases primero ---

class Task(ft.Column):
    def __init__(self, task_name, task_value, task_type, parent_column, rewards_column, on_change_callback):
        super().__init__()
        self.task_name = task_name
        self.task_value = task_value
        self.task_type = task_type
        self.parent_column = parent_column # Referencia a la columna padre para poder borrarse
        self.rewards_column = rewards_column
        self.on_change_callback = on_change_callback # <--- La función para guardar
        
        # UI Components
        self.display_task = ft.Text(value=self.task_name, color="Black", size=16, expand=True)
        self.display_value = ft.Text(value=f"{self.task_value}", color="Black", size=16, weight="bold")
        self.edit_name = ft.TextField(expand=1, color="Black", border_color="Black", height=40, content_padding=5)
        self.edit_value = ft.TextField(width=60, color="Black", border_color="Black", height=40, content_padding=5)

        # Vista Normal
        self.display_view = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(icon=ft.Icons.CHECK_CIRCLE_OUTLINE, icon_color="Purple", on_click=self.task_completed),
                self.display_task,
                self.display_value,
                ft.PopupMenuButton(
                    icon=ft.Icons.MORE_VERT,
                    icon_color="Black",
                    items=[
                        ft.PopupMenuItem(text="Edit", icon=ft.Icons.EDIT, on_click=self.edit_clicked),
                        ft.PopupMenuItem(text="Delete", icon=ft.Icons.DELETE, on_click=self.delete_clicked),
                    ]
                ),
            ]
        )

        # Vista Edición
        self.edit_view = ft.Row(
            visible=False,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                self.edit_name,
                self.edit_value,
                ft.IconButton(icon=ft.Icons.DONE, icon_color="Purple", on_click=self.save_clicked)
            ]
        )

        self.controls = [self.display_view, self.edit_view]

    def delete_clicked(self, e):
        self.parent_column.task_delete(self) # Llamamos al padre para que nos borre

    def edit_clicked(self, e):
        self.edit_name.value = self.task_name
        self.edit_value.value = str(self.task_value)
        self.display_view.visible = False
        self.edit_view.visible = True
        self.update()

    def save_clicked(self, e):
        self.task_name = self.edit_name.value
        self.task_value = self.edit_value.value
        self.display_task.value = self.task_name
        self.display_value.value = self.task_value
        self.display_view.visible = True
        self.edit_view.visible = False
        self.update()
        self.on_change_callback() # <--- GUARDAR AUTOMÁTICAMENTE

    def task_completed(self, e):
        # Sumamos puntos
        self.rewards_column.add_points(int(self.task_value))
        # Borramos la tarea (opcional, si quieres que se quede, comenta la siguiente línea)
        #self.parent_column.task_delete(self) 

class Habit_Column(ft.Column):
    def __init__(self, habit_type: str, rewards_column, on_change_callback):
        super().__init__()
        self.habit_type = habit_type
        self.rewards_column = rewards_column
        self.on_change_callback = on_change_callback

        self.new_task = ft.TextField(hint_text="Task", expand=1, color="Black", height=40)
        self.new_task_value = ft.TextField(hint_text="Pts", width=60, color="Black", height=40)
        self.tasks = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)

        self.controls=[
            ft.Container(padding=10),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text(value=self.habit_type, size=20, weight="bold", color="Black", text_align="center")
                ]
            ),
            ft.Row([
                self.new_task, 
                self.new_task_value, 
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="Purple", icon_size=40, on_click=self.add_clicked)
            ]),
            self.tasks
        ]

    def add_clicked(self, e):
        if not self.new_task.value: return # No agregar si está vacío
        
        # Creamos la tarea pasándole self (esta columna) como padre y la función de guardar
        task = Task(
            self.new_task.value, 
            self.new_task_value.value or "0", 
            self.habit_type, 
            self, # self es 'parent_column'
            self.rewards_column,
            self.on_change_callback
        )
        self.tasks.controls.append(task)
        self.new_task.value = ""
        self.new_task_value.value = ""
        self.update()
        self.on_change_callback() # <--- GUARDAR AUTOMÁTICAMENTE

    def task_delete(self, task):
        self.tasks.controls.remove(task)
        self.update()
        self.on_change_callback() # <--- GUARDAR AUTOMÁTICAMENTE

class Reward(ft.Column):
    def __init__(self, reward_name, reward_cost, parent_column, on_change_callback):
        super().__init__()
        self.reward_name = reward_name
        self.reward_cost = reward_cost
        self.parent_column = parent_column
        self.on_change_callback = on_change_callback

        self.display_reward = ft.Text(value=self.reward_name, color="Black", size=16, expand=True)
        self.display_cost = ft.Text(value=f"{self.reward_cost}", color="Black", size=16, weight="bold")

        self.controls = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(icon=ft.Icons.CARD_GIFTCARD, icon_color="Purple", on_click=self.get_reward),
                    self.display_reward,
                    self.display_cost,
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="Black", on_click=self.delete_clicked),
                ]
            )
        ]

    def delete_clicked(self, e):
        self.parent_column.reward_delete(self)

    def get_reward(self, e):
        # Intentar comprar la recompensa
        success = self.parent_column.spend_points(int(self.reward_cost))
        if success:
             self.on_change_callback() # Guardar si la compra fue exitosa

class Rewards_Column(ft.Column):
    def __init__(self, on_change_callback):
        super().__init__()
        self.on_change_callback = on_change_callback
        self.total_points = 0 # El estado de puntos vive AQUÍ ahora, no global
        
        self.new_reward = ft.TextField(hint_text="Reward", expand=1, color="Black", height=40)
        self.new_reward_cost = ft.TextField(hint_text="Cost", width=60, color="Black", height=40)
        self.rewards_list = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        self.points_text = ft.Text(value="Total Points: 0", size=20, weight="bold", color="Black")

        self.controls=[
            ft.Container(padding=10),
            ft.Row([self.points_text], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([
                self.new_reward, 
                self.new_reward_cost, 
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color="Purple", icon_size=40, on_click=self.add_clicked)
            ]),
            self.rewards_list
        ]

    def add_clicked(self, e):
        if not self.new_reward.value: return
        reward = Reward(self.new_reward.value, self.new_reward_cost.value or "0", self, self.on_change_callback)
        self.rewards_list.controls.append(reward)
        self.new_reward.value = ""
        self.new_reward_cost.value = ""
        self.update()
        self.on_change_callback()

    def reward_delete(self, reward):
        self.rewards_list.controls.remove(reward)
        self.update()
        self.on_change_callback()

    def add_points(self, points):
        self.total_points += points
        self.update_points_display()
        self.on_change_callback()

    def spend_points(self, cost):
        if self.total_points >= cost:
            self.total_points -= cost
            self.update_points_display()
            return True
        return False

    def update_points_display(self):
        self.points_text.value = f"Total Points: {self.total_points}"
        self.update()


# --- 2. Función Principal (Main) ---

def main(page: ft.Page):
    page.title = "Habit Tracker"
    page.bgcolor = ft.Colors.GREY_400
    page.padding = 0 
    
    # 2.1 Definimos la función de guardar DENTRO de main para que vea las variables
    def guardar_datos():
        # Esta función se ejecutará cada vez que cambie algo
        try:
            data = {
                "total_points": rewards_content.total_points, # Leemos puntos de la columna
                "tasks": {
                    "personal": [{"name": t.task_name, "value": t.task_value} for t in personal_content.tasks.controls],
                    "school": [{"name": t.task_name, "value": t.task_value} for t in school_content.tasks.controls],
                    "spiritual": [{"name": t.task_name, "value": t.task_value} for t in spiritual_content.tasks.controls],
                    "goals": [{"name": t.task_name, "value": t.task_value} for t in goals.tasks.controls]
                },
                "rewards": [{"name": r.reward_name, "cost": r.reward_cost} for r in rewards_content.rewards_list.controls]
            }
            page.client_storage.set("habit_data_v2", json.dumps(data))
            # print("Datos guardados automáticamente") # Descomentar para depurar
        except Exception as e:
            print(f"Error guardando: {e}")

    # 2.2 Inicializamos las columnas pasando 'guardar_datos' como callback
    rewards_content = Rewards_Column(guardar_datos)
    
    personal_content = Habit_Column("Personal", rewards_content, guardar_datos)
    school_content = Habit_Column("School", rewards_content, guardar_datos)
    spiritual_content = Habit_Column("Spiritual", rewards_content, guardar_datos)
    goals = Habit_Column("Goals", rewards_content, guardar_datos)

    # 2.3 Función para Cargar Datos
    def cargar_datos():
        json_data = page.client_storage.get("habit_data_v2")
        
        if json_data:
            try:
                data = json.loads(json_data)
                
                # Cargar puntos
                rewards_content.total_points = data.get("total_points", 0)
                rewards_content.update_points_display()

                # Mapa para iterar fácil
                mapa_columnas = {
                    "personal": personal_content,
                    "school": school_content,
                    "spiritual": spiritual_content,
                    "goals": goals
                }

                # Cargar Tareas
                tasks_data = data.get("tasks", {})
                for key, columna in mapa_columnas.items():
                    # Limpiamos por seguridad para no duplicar si llamamos cargar dos veces
                    columna.tasks.controls.clear() 
                    
                    lista_tareas = tasks_data.get(key, [])
                    for t in lista_tareas:
                        nueva_tarea = Task(
                            t["name"], 
                            t["value"], 
                            columna.habit_type, 
                            columna, 
                            rewards_content, 
                            guardar_datos # Pasamos la función de nuevo
                        )
                        columna.tasks.controls.append(nueva_tarea)
                
                # Cargar Recompensas
                rewards_content.rewards_list.controls.clear()
                for r in data.get("rewards", []):
                    nueva_recompensa = Reward(r["name"], r["cost"], rewards_content, guardar_datos)
                    rewards_content.rewards_list.controls.append(nueva_recompensa)
                
                print("Datos cargados correctamente")
                
            except Exception as e:
                print(f"Error cargando datos: {e}")

    # 2.4 Interfaz Gráfica
    main_page = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(height=20), # Espacio superior
            ft.Text("Habit Tracker", color="Black", size=30, weight="bold", text_align="center"),
            ft.Tabs(
                tab_alignment=ft.TabAlignment.CENTER,
                label_color="Black",
                indicator_color="Purple",
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab(text="Personal",content=personal_content),
                    ft.Tab(text="School", content=school_content),
                    ft.Tab(text="Spiritual", content=spiritual_content),
                    ft.Tab(text="Goals", content=goals),
                    ft.Tab(text="Shop", icon=ft.Icons.SHOPPING_CART, content=rewards_content),
                ],
                expand=True
            )
        ]
    )

    page.add(main_page)
    
    # 2.5 ¡Cargamos los datos al iniciar!
    cargar_datos()
    page.update()

ft.app(target=main)