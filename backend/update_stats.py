# update_stats.py
import sqlite3
import argparse
import os

DB_PATH = "dashboard.db"

def ensure_db_exists():
    if not os.path.exists(DB_PATH):
        print("❌ dashboard.db não encontrado.")
        print("Rode o backend primeiro: uvicorn main:app --reload")
        exit(1)

def update_stats(online_now=None, bans_today=None, sales_today=None, reports_open=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Garante que a linha id=1 exista
    cursor.execute("SELECT id FROM overview_stats WHERE id = 1")
    row = cursor.fetchone()

    if not row:
        print("⚠️ overview_stats id=1 não existe. Criando...")
        cursor.execute("""
            INSERT INTO overview_stats (id, online_now, bans_today, sales_today, reports_open)
            VALUES (1, 0, 0, 0, 0)
        """)
        conn.commit()

    # Atualizações dinâmicas
    fields = []
    values = []

    if online_now is not None:
        fields.append("online_now = ?")
        values.append(online_now)

    if bans_today is not None:
        fields.append("bans_today = ?")
        values.append(bans_today)

    if sales_today is not None:
        fields.append("sales_today = ?")
        values.append(sales_today)

    if reports_open is not None:
        fields.append("reports_open = ?")
        values.append(reports_open)

    if fields:
        query = f"UPDATE overview_stats SET {', '.join(fields)} WHERE id = 1"
        cursor.execute(query, values)
        conn.commit()
        print("✅ Dashboard atualizado com sucesso.")
    else:
        print("⚠️ Nenhum valor informado.")

    # Mostrar valores atuais
    cursor.execute("SELECT online_now, bans_today, sales_today, reports_open FROM overview_stats WHERE id = 1")
    updated = cursor.fetchone()

    print("\n📊 Valores atuais:")
    print(f"Online agora: {updated[0]}")
    print(f"Bans hoje: {updated[1]}")
    print(f"Vendas hoje: {updated[2]}")
    print(f"Reports abertos: {updated[3]}")

    conn.close()

if __name__ == "__main__":
    ensure_db_exists()

    parser = argparse.ArgumentParser(description="Atualizar estatísticas da dashboard")
    parser.add_argument("--online", type=int, help="Online agora")
    parser.add_argument("--bans", type=int, help="Bans hoje")
    parser.add_argument("--sales", type=int, help="Vendas hoje")
    parser.add_argument("--reports", type=int, help="Reports abertos")

    args = parser.parse_args()

    update_stats(
        online_now=args.online,
        bans_today=args.bans,
        sales_today=args.sales,
        reports_open=args.reports
    )