"""data BACKEND."""
from mysql.connector import connect

class DataBase:
    '''Una base de datos de MySQL.'''
    def __init__(self, host:str = "my_host", user:str = "my_user", password:str = "my_password", database:str = "my_db") -> None:
        """Inicializa una base de datos en MySQL para enviar comandos y/o obtener datos.\n
        Nota:
        \tRequiere instalar el módulo `mysql` haciendo `pip install mysql-connector-python`."""
        self.__host = host
        self.__user = user
        self.__password = password
        self.__database = database
    
    def connection(self):
        '''Hace una conexión a la base de datos.'''
        _host = self.__host
        _user = self.__user
        _passoword = self.__password
        _database = self.__database

        return connect(host = _host, user = _user, password = _passoword, database = _database)
    
    #Ayuda a verificar si un usuario existe
    def get_data(self, table:str, columns:list[str] = []) -> list[tuple] | list:
        """Retorna una lista con todos los datos de `table`, `columns` especifica las columnas a retornar;
        si no se especifica retorna todas las columnas. Retorna `[()]` si la tabla está vacía."""

        connection = self.connection()
        cursor = connection.cursor()
        
        if not len(columns):
            cursor.execute(f"SELECT * FROM {table}")
            data = cursor.fetchall()
        else:
            
            cursor.execute(f"SELECT {", ".join(columns)} FROM {table}")
            if len(columns) == 1:
                data = []

                for dt in cursor.fetchall():
                    data.append(*dt)
            else:
                data = cursor.fetchall()
        cursor.close()
        connection.close()

        return data if data else [()]

### --- Clase útil extra para las materias --- ###
class Subject:
    '''Una clase para la materia.'''
    def __init__(self, name:str, database:DataBase) -> None:
        '''Constructor de `Subject`.\n
        El `name` es el nombre de la materia.\n
        La `database` es la base de datos.'''
        self.__name = name
        self.__database = database
    
    def is_registered(self) -> bool:
        '''Retorna True si la materia está registrada (por su `name`), False de lo contrario.'''
        return self.__name in self.__database.get_data(table="subjects", columns=["name"])
    
    def get_id(self) -> int | None:
        '''Retorna el id de la materia, None si ésta no está registrada.'''
        if not self.is_registered():
            return None
        connection = self.__database.connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT id FROM subjects WHERE name = '{self.__name}'")
        _id = cursor.fetchall()[0][0]
        cursor.close()
        connection.close()

        return _id
    
    def get_name(self) -> str | None:
        '''Retorna el nombre de la materia, None si no está registrada.'''
        return self.__name if self.is_registered() else None
    
    def has_teacher(self) -> bool | None:
        '''Retorna True si esta materia ya tiene asignada un maestro, False de lo contrario.\
            None si la materia no está registrada.'''
        if not self.is_registered():
            return None
        connection = self.__database.connection()
        cursor = connection.cursor()
        subject_id = self.get_id()
        cursor.execute("""SELECT EXISTS(
                                SELECT 1 
                                FROM teacher_subjects 
                                WHERE subject_id = %s
                            )
                        """, (subject_id, ))
        has_teacher_yet = cursor.fetchone()[0] == 1
        cursor.close()
        connection.close()

        return has_teacher_yet
### ---------------------------------------- ###

class _User:
    '''Clase padre de las clases hijas `Student` y `Teacher`.'''
    _table:str

    def __init__(self, username:str, database:DataBase) -> None:
        '''Constructor de _User.\n
        El `username` es el nombre de usuario registrado.\n
        La `database` es la base de datos.'''
        self._username = username
        self._database = database
    
    def is_registered(self) -> bool:
        '''Retorna True si el usuario está registrado (por su `username`), False de lo contrario.'''
        return self._username in self._database.get_data(table=f"{self._table}", columns=["user_name"])

    def get_id(self) -> int | None:
        '''Retorna el id del usuario, None si éste no existe.'''
        if not self.is_registered():
            return None
        
        connection = self._database.connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT id FROM {self._table} WHERE user_name = '{self._username}'")
        _id = cursor.fetchall()[0][0]
        cursor.close()
        connection.close()

        return _id
    
    def get_name(self) -> str:
        '''Retorna el nombre del usuario, None si éste no está registrado.'''
        if not self.is_registered():
            return None

        connection = self._database.connection()
        cursor = connection.cursor()

        cursor.execute(f"SELECT name from {self._table} WHERE user_name = '{self._username}'")

        name = cursor.fetchall()[0][0]

        cursor.close()
        connection.close()

        return name
    
    def get_password(self) -> str | None:
        '''
        #### AVISO: DESENCRIPTACIÓN ####
        Retorna la contraseña desemcriptada del usuario , si éste no existe retorna None.'''
        if not self.is_registered():
            return None
        
        connection = self._database.connection()
    
        cursor = connection.cursor()
        cursor.execute(f"""SELECT CONVERT(AES_DECRYPT(password, 'your_key')
                       USING UTF8) AS pd FROM {self._table} 
                       WHERE user_name = '{self._username}'""")
        decrypted_password = cursor.fetchall()[0][0]

        cursor.close()
        connection.close()
        
        return decrypted_password
    
    def get_user_name(self) -> str | None:
        '''Retorna el `user_name` del usuario, None si éste no está registrado.'''
        return self._username if self.is_registered() else None

class Student(_User):
    '''Una clase para el estudiante.'''
    def __init__(self, username:str, database:DataBase) -> None:
        '''Contructor de `Student`.\n
        El `username` es el nombre de usuario registrado.\n
        La `database` es la base de datos.'''
        super().__init__(username, database)
        self._table = "students"

    ### Ver sus materias y calificaciones
    def get_subjects(self, with_grades:bool = True) -> dict[str, float] | list[str] | None:
        '''Retorna un diccionario con los nombres de las materias y sus calificaciones si `with_grades` es True, 
        de lo contrario retorna una lista con solo los nombres de las materias.\n
        Si el estudiante no existe, retorna None.'''

        if not self.is_registered():
            return None
        
        connection = self._database.connection()
        cursor = connection.cursor()
        cursor.execute("SELECT sub.name AS subject, ss.grade AS grade\
                        FROM students s\
                        JOIN student_subjects ss ON s.id = ss.student_id\
                        JOIN subjects sub ON ss.subject_id = sub.id\
                        WHERE s.user_name = %s;", (self._username, ))
        
        subjects = dict([data for data in cursor.fetchall()])
        
        cursor.close()
        connection.close()

        return subjects if with_grades else list(subjects.keys())
    
    ### Consultar su promedio general
    def get_average(self) -> float | None:
        '''Retorna el promedio del estudiante si éste existe y tiene calificaciones, de lo contrario retorna None.'''
        if not self.is_registered() or any(grade is None for grade in self.get_subjects().values()):
            return None
    
        subs_values = self.get_subjects().values()
        average = sum(subs_values) / len(subs_values)

        return round(average, 2)
    
    ### Ver su calificación más baja
    def get_worst_grades(self) -> dict[str, float] | dict[None, None]:
        '''Retorna un diccionario con las materias y calificaciones más bajas o, 
        un diccionario con clave y valor None si el estudiante no existe.'''
        if not self.is_registered() or any(grade is None for grade in self.get_subjects().values()):
            return {None: None}
        
        min_grade = min(self.get_subjects().values())
        worst_grades = {}

        for subject, grade in self.get_subjects().items():
            if grade == min_grade:
                worst_grades[subject] = grade
        
        return worst_grades
    
    ### Situación aprobatoria?
    def is_passed(self) -> bool | None:
        '''Retorna True si la situación del estudiante es aprobatoria de acuerdo a su promedio,
        de lo contrario retorna False.\n
        Retorna None si el estudiante no tiene calificaciones.'''
        if not self.is_registered() or any(grade is None for grade in self.get_subjects().values()):
            return None
        
        return self.get_average() >= 60.0
    
    ### ---- Métodos útiles extra ---- ###
    def get_career(self) -> str:
        '''Retorna la carrera del estudiante, None si el estudiante no está registrado.'''
        if not self.is_registered():
            return None
        
        connection = self._database.connection()
        cursor = connection.cursor()

        cursor.execute("""SELECT c.name
                            FROM students s
                            JOIN careers c ON s.career_id = c.id
                            WHERE s.user_name = %s
                        """, (self._username, ))

        career = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()

        return career
    
    def get_group(self) -> str:
        '''Retorna el grupo del estudiante, None si el estudiante no está registrado.'''
        if not self.is_registered():
            return None
        
        connection = self._database.connection()
        cursor = connection.cursor()

        student_id = self.get_id()
        cursor.execute(f"SELECT _group FROM students WHERE id = {student_id}")

        group = cursor.fetchall()[0][0]

        cursor.close()
        connection.close()

        return group
    
    def assigned_subject_yet(self, subject:Subject) -> bool | None:
        '''Retorna True si la el estudiante ya está asignado a esta materia.\n
        None si el estudiante no está registrado'''

        if not self.is_registered():
            return None
        
        return subject.get_name() in self.get_subjects(with_grades=False)

class Teacher(_User):
    '''Una clase para el maestro.'''
    def __init__(self, username:str, database:DataBase):
        '''Contructor de `Teacher`.\n
            El `username` es el nombre de usuario del maestro.\n
            La `database` es la base de datos.'''
        super().__init__(username, database)
        self._table = "teachers"
    
    ### Agregar alumnos
    def add_student(self, student:Student, subject:Subject) -> None:
        '''Agrega el estudiante `student` a la materia `subject`.'''

        if not self.is_registered():
            raise ValueError("Maestro no registrado.")
        
        if not student.is_registered():
            raise ValueError("El estudiante no está registrado.")
        
        connection = self._database.connection()
        cursor = connection.cursor()

        student_id = student.get_id()
        subject_id = subject.get_id()

        cursor.execute(f"INSERT INTO student_subjects (student_id, subject_id) VALUES ({student_id}, {subject_id})")

        connection.commit()
        cursor.close()
        connection.close()

        return None
    
    ### Organizar alumnos
    def set_group(self, student:Student, group:str, career:str) -> None:
        '''Asigna el grupo `group` al estudiante `student` .'''
        if not student.is_registered() or not group.isalpha() or len(group) > 1:
            raise ValueError("Estudiante no registrado y/o el grupo no es válido.")
        
        connection = self._database.connection()
        cursor = connection.cursor()

        student_id = student.get_id()
        cursor.execute(f"UPDATE students SET _group = '{group}', career = '{career}' WHERE id = {student_id}")
        
        connection.commit()
        cursor.close()
        connection.close()

        return None

    ### Registrar materias nuevas
    def add_subject(self, subject:Subject) -> None:
        '''Registra la materia `subject`.'''
        if not self.is_registered() or not subject.is_registered():
            raise ValueError("Maestro o materia erróneos.")
        
        connection = self._database.connection()
        cursor = connection.cursor()

        teacher_id = self.get_id()
        subject_id = subject.get_id()
        cursor.execute(f"INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ({teacher_id}, {subject_id})")

        connection.commit()
        cursor.close
        connection.close()

        return None
    
    ### Asignar o modificar calificaciones
    def set_grade(self, grade:float, subject:Subject, student:Student) -> None:
        '''Asigna o modifica la calificación `grade` de la materia `subject` al estudiante `student`.'''
        if (grade < 0.0 or grade > 100.0) or not self.is_registered() or not subject.is_registered() or not student.is_registered():
            raise ValueError("Datos erróneos.")
        
        connection = self._database.connection()
        cursor = connection.cursor()

        student_id = student.get_id()
        subject_id = subject.get_id()
        cursor.execute(f"UPDATE student_subjects SET grade = {grade} WHERE student_id = {student_id} AND subject_id = {subject_id}")
        
        connection.commit()
        cursor.close()
        connection.close()

        return None
    
    ### Consultar listado de alumnos
    def get_students(self, users_only:bool = True) -> list[tuple]:
        '''Retorna una lista con los estudiantes del maestro: nombre, usuario, materia, carrera y su grupo si `users_only` es False,
        de lo contrario retorna sólo una lsita con sólo los usuarios de los alumnos'''
        if not self.is_registered():
            raise ValueError("Maestro no registrado.")

        connection = self._database.connection()
        cursor = connection.cursor()

        if not users_only:
            cursor.execute(f"""SELECT 
                                s.name AS alumno,
                                s.user_name,
                                sub.name AS materia,
                                c.name AS carrera,
                                s._group AS grupo
                                FROM teachers t
                                JOIN teacher_subjects ts ON t.id = ts.teacher_id
                                JOIN subjects sub ON ts.subject_id = sub.id
                                JOIN student_subjects ss ON sub.id = ss.subject_id
                                JOIN students s ON ss.student_id = s.id
                                JOIN careers c ON s.career_id = c.id
                                WHERE t.user_name = '{self._username}'
                                ORDER BY sub.name, s._group, s.name
                            """)
            students = cursor.fetchall()
        else:
           
            cursor.execute(f"""SELECT DISTINCT s.user_name
                                FROM teachers t
                                JOIN teacher_subjects ts ON t.id = ts.teacher_id
                                JOIN student_subjects ss ON ts.subject_id = ss.subject_id
                                JOIN students s ON ss.student_id = s.id
                                WHERE t.user_name = '{self._username}'
                            """)
            students = []
            for user in cursor.fetchall():
                students.append(*user)

        cursor.close()
        connection.close()
        
        return students
    
    ###  ---- Métodos útiles extra ---- ####
    def get_subjects(self) -> str:
        '''Retorna las materias asignadas del maestro.'''

        if not self.is_registered():
            raise ValueError("Maestro no registrado.")
        
        connection = self._database.connection()
        cursor = connection.cursor()

        cursor.execute(f"SELECT sub.name FROM teachers t\
                        JOIN teacher_subjects ts ON t.id = ts.teacher_id\
                        JOIN subjects sub ON ts.subject_id = sub.id\
                        WHERE t.user_name = '{self._username}'")
        
        subjects = []

        for subject in cursor.fetchall():
            subjects.append(*subject)
        
        cursor.close()
        connection.close()

        return subjects
