from shiny import App, ui, render, reactive
import requests
import os

API_URL = os.getenv("API_URL", "https://localhost:8000")

def api_request(endpoint, method="GET", data=None, token=None, use_form_data=False):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"{API_URL}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        if use_form_data:
            response = requests.post(url, data=data, headers=headers)
        else:
            response = requests.post(url, json=data, headers=headers)
    elif method == "PUT":
        reponse = requests.put(url, json=data, headers=headers)
    elif method == "DELETE":
        reponse = requests.delete(url, headers=headers)

    response.raise_for_status()

    return response.json() if response.content else None



#ui
app_ui = ui.page_fluid (
    ui.panel_title("time tracker"),

    #have to render reactive values for shiny to take them seriously apparently 
    ui.div(
        ui.output_text("is_logged_in"),
        style="font-size: 1px; color: white; opacity: 0;"
    ),

    ui.div(

    ui.output_text("show_project_form"),
    style="font-size: 1px; color: white; opacity: 0;"
    ),

    ui.div(ui.output_text("has_active_timer"),
           style="font-size: 1px; color: white; opacity: 0;"
    ),

    ui.panel_conditional("output.is_logged_in == 'false'",
    ui.card(
        ui.card_header("Login"),
        ui.input_text("username", "Username"),
        ui.input_password("password", "Password"),
        ui.input_action_button("login_btn", "Login", class_="btn-primary"),
        ui.output_text("login_error")
    )
),

    ui.panel_conditional("output.is_logged_in == 'true'",
        ui.card(
        ui.card_header("dashboard"),

        #project selection handling
        ui.input_action_button("new_project_btn", "New Project", class_="btn-primary"),

        # new project form (show/hide)
        ui.panel_conditional("output.show_project_form == 'true'",
            ui.card(
                ui.card_header("Create New Project"),
                ui.input_text("project_name", "Project Name"),
                ui.input_text_area("project_description", "Description (optional)"),
                ui.input_text("project_color", "Color (hex)", value="#3b82f6"),
                ui.input_action_button("create_project_btn", "Create Project", class_="btn-success")
            )
        ),

        ui.input_select("selected_project", "Select Project:", choices={}),
        ui.p("Total Time (minutes) for Selected Project:"),
        ui.output_text("selected_project_total"),


        #timer controls
        ui.panel_conditional(
            "output.has_active_timer == 'false'",
            ui.input_action_button("start_timer_btn", "Start Timer", class_="btn-success")
        ),
        ui.panel_conditional(
            "output.has_active_timer == 'true'",
            ui.input_action_button("stop_timer_btn", "Stop Timer", class_="btn-danger")
        ),  
        ui.hr(),

        #log out button 
        ui.input_action_button("logout_btn", "Logout", class_="btn-danger")
    )
    ) 

) #close page ui description


def server(input, output, session):
    token = reactive.Value(None)
    error_message = reactive.Value("")
    projects = reactive.Value([])
    _show_project_form = reactive.Value(False)
    project_refresh_trigger = reactive.Value(0)
    active_timer = reactive.Value(None) 
    time_entries = reactive.Value([])
    timer_refresh_trigger = reactive.Value(0)


    #login / auth methods
    @output
    @render.text
    def is_logged_in():
        return "true" if token.get() else "false"


    @reactive.Effect
    @reactive.event(input.login_btn)
    def handle_login():
        try:
            response = api_request("/auth/token", method="POST", data={
                "username": input.username(),
                "password": input.password()
            }, use_form_data=True)
            token.set(response.get("access_token"))
            error_message.set("")
        except requests.exceptions.HTTPError as e:
            error_message.set("Login failed. Please check your credentials.")
            token.set(None)

    @reactive.Effect
    @reactive.event(input.logout_btn)
    def handle_logout():
        token.set(None)

    @output
    @render.text
    def login_error():
        msg = error_message.get()
        if msg:
            return msg
        return ""
    
    @output
    @render.text
    def debug_login_status():
        return f"is_logged_in returns: {is_logged_in()}"


    # projects methods

    @output 
    @render.text
    def show_project_form():
        return "true" if _show_project_form.get() else "false"
    

    @reactive.Effect
    def fetch_projects():
        project_refresh_trigger.get()  
        if token.get():
            try:
                response = api_request("/projects/", method="GET", token=token.get())
                projects.set(response)
            except requests.exceptions.HTTPError as e:
                error_message.set("Failed to fetch projects.")


    @reactive.Effect
    def update_project_list():

        project_list = projects.get()
        choices = {project['id']: project['name'] for project in project_list}
        ui.update_select("selected_project", choices=choices)      
    
    @reactive.Effect
    @reactive.event(input.new_project_btn)
    def toggle_project_form():
        print('new project button clicked')
        cur_status = _show_project_form.get()
        print('current status: ', cur_status)
        _show_project_form.set(not _show_project_form.get())
        print('new status: ', _show_project_form.get())
    
    @reactive.Effect
    @reactive.event(input.create_project_btn)
    def create_project():
        try:
            name = input.project_name()
            description = input.project_description()
            color = input.project_color()

            api_request("/projects/", method="POST", token=token.get(), data={"name" : name, "description" : description, "color" : color})

            _show_project_form.set(False)
            project_refresh_trigger.set(project_refresh_trigger.get() + 1)
        except requests.exceptions.HTTPError as e:
            error_message.set("Failed to create project")


    # time entry methods

    @reactive.Effect
    def fetch_time_entries():
        timer_refresh_trigger.get()
        if token.get():
            try:
                response = api_request("/time-entries/", method="GET", token=token.get())
                time_entries.set(response)
            except requests.exceptions.HTTPError as e:
                error_message.set("Failed to fetch time entries.")

    @output
    @render.text
    def has_active_timer():
        return "true" if active_timer.get() is not None else "false"

    @reactive.Effect
    @reactive.event(input.start_timer_btn)
    def start_timer():
        print("start clicked")
        try:
            project = input.selected_project()
            timer = api_request("/time-entries/start", method="POST", token=token.get(), data={"project_id": project} )
            active_timer.set(timer)

        except requests.exceptions.HTTPError as e:
            error_message.set("failed to start timer")

    @reactive.Effect
    @reactive.event(input.stop_timer_btn)
    def stop_timer():
        print("stop clicked")
        try:
            api_request(f"/time-entries/{active_timer.get()['id']}/stop", method="POST", token=token.get(), data={})
            active_timer.set(None)
            timer_refresh_trigger.set(timer_refresh_trigger.get() + 1)
        except requests.exceptions.HTTPError as e:
            error_message.set("failed to stop timer")


    @output
    @render.text
    def selected_project_total():
        if input.selected_project() is None:
            return "0"
        project = int(input.selected_project())
        entries = time_entries.get()

        total_time_min = sum(
            entry['duration_minutes'] 
            for entry in entries
            if entry['project_id'] == project and entry['duration_minutes'] is not None
        )
       
        return total_time_min
    

        

    # debug tools/helpers
    
    @output
    @render.text
    def test_output():
        return "hello"
    


app = App(app_ui, server)

