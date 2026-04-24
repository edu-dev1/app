"""app BACKEND"""
# Importar las funciones, variables y clases necesarias
from flask import Flask, render_template, request, session, redirect, url_for, Response, abort
from data_backend import DataBase, Student, Subject, Teacher

# Crear el objeto principal de Flask, la aplicación con el nombre "__main__" (__name__)
app = Flask(__name__)
# Una clave secreta (no compartir) para proteger datos al usar sesiones y cookies
app.secret_key = ""
# Crear el objeto de la base de datos
db = DataBase(host="my_host", user="my_user", password="my_password", database="my_db") 
# ---------------------------------------------------- #
### --- PÁGINA (1) PARA ELEGIR EL MODO --- ###
@app.route('/login_mode', methods=["GET", "POST"])
def show_loginmode_page() -> Response | str:
    if request.method == "POST":
        mode = request.form.get("mode")  # student o teacher
        session["mode"] = mode           # Guardando el modo
        return redirect(url_for("show_login_page")) # Redireccionando a la función (página) para iniciar sesión

    return render_template("select_mode.html") # Cuando el método es GET (siempre se ejecuta GET) muestra ese .html

# ---------------------------------------------------- #
### --- PÁGINA (2) PARA INICIAR SESIÓN --- ###
@app.route('/login', methods = ["GET", "POST"])
def show_login_page() -> Response | str:

    mode = session.get("mode")  # Guarda el modo teacher o estudiante

    if request.method == "POST": # Si el método o petición es POST...
        if mode == "student": # ... Si el modo es de estudiante...
            # ... obtiene el usuario y la contraseña del esetudiante y...
            usuario_estudiante = request.form.get("usuario")
            contraseña_estudiante = request.form.get("contraseña")
            # ... crea un objeto estudiante para...
            student = Student(username = usuario_estudiante, database = db)
            # ... checar que su usuario y contraseña sean correctos con los datos de la base de datos inicializada al inicio
            if student.is_registered() and contraseña_estudiante == student.get_password():
                # Si todo fue correcto, inicia la sesión y el modo, y...
                session["user"] = usuario_estudiante
                session["mode"] = "student"
                # ... redirije a la función que muestra el menú del estudiante.
                return redirect(url_for("show_student_menu"))
            else: # Si todo no fue correcto...
                abort(500) # ... llama al código de petición de HTTP número 500 
            
        elif mode == "teacher": # Si el modo es de maestro...
            # ... obtiene el usuario y contraseña del maestro y...
            usuario_maestro = request.form.get("usuario")
            contraseña_maestro = request.form.get("contraseña")
            # ... crea un objeto maestro para...
            teacher =  Teacher(username = usuario_maestro, database = db)
            # ... checar que su usuario y contraseña sean correctos con los datos de la base de datos inicializada al inicio
            if teacher.is_registered() and contraseña_maestro == teacher.get_password():
                # Si todo fue correcto, inicia la sesión y el modo, y...
                session["user"] = usuario_maestro
                session["mode"] = "teacher"
                # redirige a la función que muestra el menú del maestro.
                return redirect(url_for("show_teacher_menu"))
            else: # Si todo no fue correcto...
                abort(500) # ... llama al código de petición de HTTP número 500
    
    if "mode" not in session: #Si no han elegido el modo de inicio de sesión...
        abort(403) # ... llama al código de petición de HTTP número 403
    
    return render_template("login.html") # Muestra este .html cuando la petición o método es GET (siempre)

# ---------------------------------------------------- #
### --- MANEJO DE ERRORES (CÓDIGOS DE PETICIONES DE HTTP) --- ###
# Estas 3 funciones muestran diferentes páginas al encontrar los códigos 404, 500 y 403
@app.errorhandler(404) # Código 404 significa: página no encontrada
def show_404_error(error) -> str:
    return render_template("404.html", error = error), 404

@app.errorhandler(500) # Código 500 significa: error de inicio de sesión (usuario o contraseña incorrectos)
def show_500_error(error) -> str:
    return render_template("500.html", error = error), 500

@app.errorhandler(403) # Código 403 significa: debes iniciar sesión para esto
def show_404_error(error) -> str:
    return render_template("403.html", error = error), 403

# ---------------------------------------------------- #
### MENÚS ###
# Estas 2 funciones muestras los menús del estudiante y maestro
@app.route('/student_menu') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def show_student_menu() -> str:
    if "user" not in session: # Si no han iniciado sesión no puede ver esta página y ...
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "student": # Si no es estudiante...
        return render_template("error_student.html") # ... muestra plantilla de error.
    
    student = Student(session["user"], db) # Crea el objeto estudiante con el usuario de la sesión iniciada
    # Obtiene toda la información y la carrera del estudiante porque...
    data = student.get_info(columns=["name", "age", "user_name", "semester", "_group"])
    career = student.get_career()
    return render_template("student_menu.html", info = data, carrera = career) #... esta plantilla .html lo necesita

@app.route('/teacher_menu') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def show_teacher_menu() -> str:
    if "user" not in session: # Si no han iniciado sesión no puede ver esta página y ...
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "teacher": # Si no es maestro...
        return render_template("error_teacher.html") # ... muestra plantilla de error.
    
    teacher = Teacher(session["user"], db) # Crea el objeto maestro con el usuario de la sesión iniciada
    
    data = teacher.get_info(["name", "age", "user_name",]) # Obtiene el nombre del maestro porque...
    return render_template("teacher_menu.html", info = data) # esta plantilla .html lo necesita

# ---------------------------------------------------- #
### CERRAR SESIÓN ###
# Está función cierra la sesión
@app.route('/logout') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def logout() -> Response:
    session.clear() # Limpia (borra) la sesión y ...
    return redirect(url_for("show_loginmode_page")) # ... redirige a esta función que muestra la página (1)

# ---------------------------------------------------- #
### ESTUDIANTE ###
# Estas 4 páginas son para mostrar los datos del estudiante
# Esta primera función muestra la página de las materias con sus calificiaciones
@app.route('/subjects') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def show_subjects_grades() -> str:
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición
    
    if not session["mode"] == "student": # Si no es estudiante...
        return render_template("error_student.html") # ... muestra plantilla de error.
    
    student = Student(session["user"], db) # Crea el objeto estudiante con el usuario de la sesión iniciada

    subjects = student.get_subjects(with_grades = True) # Obtiene las materias con calificaciones del estudiante porque...
    
    return render_template("subjects.html", materias = subjects) # ... esta platilla .html las necesita.

# Esta función muestra la página del promedio del estudiante
@app.route('/average') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def show_average() -> str:
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "student": # Si no es estudiante...
        return render_template("error_student.html") # ... muestra plantilla de error.
    
    student = Student(session["user"], db) # Crea el objeto estudiante con el usuario de la sesión iniciada
    average = student.get_average() # Obtiene el promedio del estudiante porque...

    return render_template("average.html", promedio = average) # esta plantilla .html lo necesita.

# Esta función muestra la página de las peores calificaciones del estudiante
@app.route('/worst_grade') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def show_worst_grades() -> str:
    
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "student": # Si no es estudiante...
        return render_template("error_student.html") # ... muestra plantilla de error.
    
    student = Student(session["user"], db) # Crea el objeto estudiante con el usuario de la sesión iniciada
    worst_grades = student.get_worst_grades() # Obtiene las peores calificaciones (materia y calificación) del estudiante porque...

    return render_template("worst_grades.html", datos = worst_grades) # esta plantilla .html las necesita.

# Esta función muestra la página del estado del estudiante
@app.route('/status') # Este método decorador "route" es para nombrar la ruta o url de la página que mostrará esta función
def show_status() -> str:
    
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "student": # Si no es estudiante...
        return render_template("error_student.html") # ... muestra plantilla de error.
    
    student = Student(session["user"], db) # Crea el objeto estudiante con el usuario de la sesión iniciada
    status = "Aprobado" if student.is_passed() else "Reprobado" # Guarda el estado del estudiante porque...

    return render_template("status.html", estado = status) # ... esta plantilla .html lo necesita.

# ---------------------------------------------------- #
### MAESTRO ###
# Estas 5 funciones son para mostrar las páginas del maestro
# El método o petición GET es para obtener datos del servidor (mostrar la página).
# El método o petición POST es para mandarle datos al servidor (editar los datos de los alumnos).
# Esta primera función muestra la página (GET) para agregar un nuevo estudiante a una materia del maestro (POST).
@app.route('/add_student', methods = ["GET", "POST"])
def show_add_student() -> str:
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "teacher": # Si no es maestro...
        return render_template("error_teacher.html") # ... muestra plantilla de error.

    teacher = Teacher(session["user"], db) # Crea el objeto maestro con el usuario de la sesión iniciada

    if request.method == "POST": # Si la petición es POST
        
        # Obtiene el usuario y la materia del estudiante
        user_student = request.form.get("usuario")
        name_subject = request.form.get("materia")
        # Crea los objetos estudiante y materia 
        student = Student(user_student, db)
        subject = Subject(name_subject, db)

        subject_name = subject.get_name()
        student_user = student.get_user_name()

        if student.assigned_subject_yet(subject): #Si el alumno ya está en la materia...
            
            return render_template("warning_student.html",
                            usuario = student_user,
                            materia = subject_name) # ... muestra esta plantilla de aviso
            
        else:
            # Agrega al estudiante a la materia
            teacher.add_student(student, subject)
            
            return redirect(url_for("show_add_student")) # Redirige a esta misma función para que muestre otra vez la misma página
    
    # Obtiene los usuarios y materias del maestro porque ...
    users = teacher.get_students(users_only=True) 
    subjects = teacher.get_subjects()

    return render_template("add_student.html", # ... esta platilla .html los necesita.
                           usuarios = users,
                           materias = subjects)

# Esta función muestra la página de organizar estudiantes
@app.route('/org_student', methods = ["GET", "POST"])
def show_organize_student() -> str:
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición
    
    if not session["mode"] == "teacher": # Si no es maestro...
        return render_template("error_teacher.html") # ... muestra plantilla de error.
    
    teacher = Teacher(session["user"], db) # Crea el objeto maestro con el usuario de la sesión iniciada

    if request.method == "POST": # Si la petición es POST

        # Obtiene el usuario del estudiante y crea un objecto estudiante
        user_student = request.form.get("usuario")
        student = Student(user_student, db)
        # Obtiene la carrera y el grupo
        career = request.form.get("carrera")
        group = request.form.get("grupo")

        if not career: # Si no eligieron una carrera...
            career = student.get_career() # ... la carrera sigue siendo la misma
        if not group: # Si no eligieron un grupo ...
            group = student.get_info("_group") # ... el grupo sigue siendo el mismo porque...

        teacher.set_group_career(student, group, career) # ... este método se ejecuta siempre.
        
        return redirect(url_for("show_organize_student")) # Redirige a esta misma función para que muestre otra vez la página

    # Obtiene los estudiantes con toda su información disponible, los usuarios y las carreras disponibles porque...
    students = teacher.get_students(users_only=False)
    users = teacher.get_students()
    carrers = db.get_data(table="careers", columns=["name"]) 

    return render_template("org_student.html", # Esta plantilla .html los necesita.
                           estudiantes = students,
                           usuarios = users,
                           carreras = carrers)

# Esta función muestra la página para registrar más materias al profesor
@app.route("/register_subjects", methods = ["GET", "POST"])
def show_regs_subjects() -> str:
    
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición
    
    if not session["mode"] == "teacher": # Si no es maestro...
        return render_template("error_teacher.html") # ... muestra plantilla de error.
    
    teacher = Teacher(session["user"], db) # Crea el objeto maestro con el usuario de la sesión iniciada

    if request.method == "POST": # Si la petición es POST
        
        # Obtiene el nombre de la materia y crea un objeto materia 
        subject_name = request.form.get("materia")
        subject = Subject(subject_name, db)
        if subject.has_teacher(): # Si la materia ya tiene aisgnado un maestro...
            return render_template("warning_teacher.html", # ... muestra esta platilla
                                   materia = subject.get_name())
        else:
            # Agrega esa materia a la lista de materias del maestro
            teacher.add_subject(subject)

            return redirect(url_for("show_regs_subjects")) # Redirige a esta misma función para que muestre otra vez la página
    
    # Obtiene las materias del maestro y todas las materias disponibles porque...
    teachers_subjects = teacher.get_subjects()
    all_subjects = db.get_data(table="subjects", columns=["name"])

    return render_template("reg_subjects.html", materias_maestro = teachers_subjects, materias = all_subjects)# esta plantilla .html las necesita.

# Esta función muestra la página de poner calificaciones a sus estudiantes
@app.route('/set_grades', methods = ["GET", "POST"])
def show_set_grades() -> str:
    
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición
    
    if not session["mode"] == "teacher": # Si no es maestro...
        return render_template("error_teacher.html") # ... muestra plantilla de error.
    
    teacher = Teacher(session["user"], db) # Crea el objeto maestro con el usuario de la sesión iniciada

    if request.method == "POST": # Si la petición es POST
        
        # Obtiene el usuario del estudiante y crea un objecto estudiante
        student_name = request.form.get("usuario")
        student = Student(student_name, db)
        # Obtiene el nombre de la materia y crea un objeto materia
        subject_name = request.form.get("materia")
        subject = Subject(subject_name, db)
        # Obtiene la calificación de tipo float
        grade = request.form.get("calificación", type=float)    
        
        if student.assigned_subject_yet(subject): # Si el estudiante está registrado en la materia...
            teacher.set_grade(grade, subject, student) #... pone la calificación
        else: # Si no está registrado en la materia muestra una página de aviso.
            return render_template("error_grades.html", usuario = student.get_user_name(), materia = subject_name)

        return redirect(url_for("show_set_grades")) # Redirige a esta misma función para que muestre otra vez la página
    
    # Obtiene los usuarios de los estudiantes y las materias del maestro porque...
    users = teacher.get_students(users_only=True)
    subjects = teacher.get_subjects()
    
    return render_template("set_grades.html", usuarios = users, materias = subjects)# ... esta plantilla .html los necesita.

# Esta función muestra la página de la lista de los estudiantes
@app.route('/list_of_students')
def show_students():
    
    if "user" not in session: # si no ha iniciado sesión
        abort(403) # llama a este código de petición de petición

    if not session["mode"] == "teacher": # Si no es maestro...
        return render_template("error_teacher.html") # ... muestra plantilla de error.
    
    teacher = Teacher(session["user"], db) # Crea el objeto maestro con el usuario de la sesión iniciada
    
    students = teacher.get_students(users_only=False) # Obtiene los estudiantes con toda su información disponible

    return render_template("students.html", estudiantes = students) # Redirige a esta misma función para que muestre otra vez la página

if __name__ == "__main__":
    app.run(debug=True) # debug activado para que se actualicen los cambios en tiempo real (127.0.0.1:5000)
    #app.run(host="0.0.0.0", port=5000) # Para compartir en el internet local (IP_de_tu_laptop:5000)
