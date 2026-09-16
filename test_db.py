import database
try:
    db = database.DBManager()
    print("Conexion a Supabase Exitosa!")
    print("Usuarios y saldos:", db.get_all_cash())
except Exception as e:
    print("Error conectando a Supabase:", str(e))
