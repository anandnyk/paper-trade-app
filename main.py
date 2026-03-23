import flet as ft
import yfinance as yf
import asyncio

def main(page: ft.Page):
    page.title = "Habit Tracker Trade"
    page.theme_mode = "light"
    page.window_width = 400
    page.window_height = 700

    # --- LOCAL STORAGE SETUP ---
    # Check if the phone has saved data; if not, start with 2,00,000
    saved_balance = page.client_storage.get("wallet_balance")
    wallet_balance = saved_balance if saved_balance is not None else 200000.0
    
    current_position = None    
    entry_price = 0.0
    target_price = 0.0
    sl_price = 0.0
    qty = 50  

    # --- UI ELEMENTS ---
    price_text = ft.Text("Live Price: Loading...", size=32, weight="bold")
    balance_text = ft.Text(f"Wallet: ₹{wallet_balance:.2f}", size=20, color="blue")
    status_text = ft.Text("No active trades.", size=16, color="grey")
    
    target_input = ft.TextField(label="Target Price", width=150, keyboard_type="number")
    sl_input = ft.TextField(label="Stop Loss", width=150, keyboard_type="number")

    # --- TRADING LOGIC ---
    def close_trade(exit_price, reason):
        nonlocal current_position, wallet_balance
        
        if current_position == "BUY":
            profit = (exit_price - entry_price) * qty
        else:
            profit = (entry_price - exit_price) * qty

        wallet_balance += profit
        
        # Save the new balance to the phone's memory
        page.client_storage.set("wallet_balance", wallet_balance)
        
        balance_text.value = f"Wallet: ₹{wallet_balance:.2f}"
        current_position = None
        status_text.value = f"Trade closed ({reason}). P&L: ₹{profit:.2f}"
        
        target_input.value = ""
        sl_input.value = ""
        page.update()

    def place_order(order_type):
        nonlocal current_position, entry_price, target_price, sl_price
        
        if current_position is not None:
            status_text.value = "You already have an open trade!"
            page.update()
            return

        try:
            target_price = float(target_input.value)
            sl_price = float(sl_input.value)
        except ValueError:
            status_text.value = "Please enter valid numbers."
            page.update()
            return

        current_position = order_type
        entry_price = float(price_text.value.split("₹")[1])
        status_text.value = f"{order_type} placed at ₹{entry_price}."
        page.update()

    def buy_click(e): place_order("BUY")
    def sell_click(e): place_order("SELL")

    # --- RESET ACCOUNT BUTTON ---
    def reset_account(e):
        nonlocal wallet_balance
        wallet_balance = 200000.0
        page.client_storage.set("wallet_balance", wallet_balance)
        balance_text.value = f"Wallet: ₹{wallet_balance:.2f}"
        status_text.value = "Account reset to ₹2,00,000."
        page.update()

    # --- BACKGROUND ENGINE ---
    async def update_price():
        while True:
            try:
                ticker = yf.Ticker("^NSEI")
                live_price = ticker.fast_info['last_price']
                price_text.value = f"Live Price: ₹{live_price:.2f}"

                if current_position == "BUY":
                    if live_price >= target_price: close_trade(live_price, "Target Hit")
                    elif live_price <= sl_price: close_trade(live_price, "Stop Loss Hit")
                elif current_position == "SELL":
                    if live_price <= target_price: close_trade(live_price, "Target Hit")
                    elif live_price >= sl_price: close_trade(live_price, "Stop Loss Hit")

                page.update()
            except Exception:
                pass 
            await asyncio.sleep(2) 

    # --- BUILD SCREEN ---
    page.add(
        ft.Column([
            price_text,
            balance_text,
            ft.Divider(),
            ft.Row([target_input, sl_input], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([
                ft.ElevatedButton("BUY (Call)", on_click=buy_click, bgcolor="green", color="white"),
                ft.ElevatedButton("SELL (Put)", on_click=sell_click, bgcolor="red", color="white")
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Divider(),
            status_text,
            ft.Container(height=50), # Spacer
            ft.TextButton("Reset Account", on_click=reset_account, icon=ft.icons.REFRESH)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    page.run_task(update_price)

ft.app(target=main)
