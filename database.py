import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class DBManager:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set as environment variables.")
        self.supabase: Client = create_client(url, key)
        self._ensure_initial_users()

    def _ensure_initial_users(self):
        # We assume the SQL script already created the users, or we do a quick check
        try:
            for user in ["Juan David", "Sebastian"]:
                res = self.supabase.table("account").select("*").eq("user_name", user).execute()
                if not res.data:
                    self.supabase.table("account").insert({"user_name": user, "cash": "10000.00"}).execute()
        except Exception as e:
            print(f"Warning: could not ensure users. {e}")

    def get_cash(self, user_name: str) -> str:
        res = self.supabase.table("account").select("cash").eq("user_name", user_name).execute()
        return res.data[0]["cash"] if res.data else "0.00"
        
    def get_all_cash(self) -> dict:
        res = self.supabase.table("account").select("user_name, cash").execute()
        return {row["user_name"]: row["cash"] for row in res.data}

    def update_cash(self, user_name: str, new_cash: str):
        self.supabase.table("account").update({"cash": new_cash}).eq("user_name", user_name).execute()

    def get_position(self, user_name: str, symbol: str) -> tuple:
        res = self.supabase.table("positions").select("shares, total_cost").eq("user_name", user_name).eq("symbol", symbol).execute()
        if res.data:
            return (res.data[0]["shares"], res.data[0]["total_cost"])
        return None

    def upsert_position(self, user_name: str, symbol: str, shares: str, total_cost: str):
        # Supabase provides upsert based on Primary Key (user_name, symbol)
        data = {
            "user_name": user_name,
            "symbol": symbol,
            "shares": shares,
            "total_cost": total_cost
        }
        self.supabase.table("positions").upsert(data).execute()

    def delete_position(self, user_name: str, symbol: str):
        self.supabase.table("positions").delete().eq("user_name", user_name).eq("symbol", symbol).execute()

    def add_transaction(self, user_name: str, tx_type: str, symbol: str, shares: str, price: str, total: str, notes: str, timestamp: str = None):
        data = {
            "user_name": user_name,
            "type": tx_type,
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "total": total,
            "notes": notes
        }
        if timestamp:
            data["timestamp"] = timestamp
        self.supabase.table("transactions").insert(data).execute()

    def get_all_positions(self, user_name: str = None) -> list:
        if user_name:
            res = self.supabase.table("positions").select("symbol, shares, total_cost, user_name").eq("user_name", user_name).execute()
        else:
            res = self.supabase.table("positions").select("symbol, shares, total_cost, user_name").execute()
        return [(row["symbol"], row["shares"], row["total_cost"], row["user_name"]) for row in res.data]

    def get_user_transactions(self, user_name: str) -> list:
        res = self.supabase.table("transactions").select("timestamp, type, symbol, shares, price, total, notes").eq("user_name", user_name).order("id", desc=True).execute()
        return [(row["timestamp"], row["type"], row["symbol"], row["shares"], row["price"], row["total"], row["notes"]) for row in res.data]

    def reset_account(self, user_name: str):
        self.supabase.table("transactions").delete().eq("user_name", user_name).execute()
        self.supabase.table("positions").delete().eq("user_name", user_name).execute()
        self.supabase.table("account").update({"cash": "10000.00"}).eq("user_name", user_name).execute()
