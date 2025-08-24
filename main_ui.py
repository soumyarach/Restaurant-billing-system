import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import csv
import json
import datetime
import webbrowser
from urllib.parse import quote_plus

# Paths
DB_PATH = os.path.join("db","restaurant.db")
MENU_CSV = os.path.join("data","menu.csv")
SAMPLE_JSON = os.path.join("data","sample_bill.json")
SALES_CSV = os.path.join("data","sales_report.csv")

# UPI info
UPI_ID = "racharlas183-1@oksbi"
UPI_NAME = "BharatBhojan"

def load_image(path, size=None):
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    if size:
        img = img.resize(size, Image.ANTIALIAS)
    return ImageTk.PhotoImage(img)

class RestaurantBillingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bharat Bhojan • Restaurant Billing")
        self.geometry("1000x700")
        self.configure(bg="#f5f5f5")

        # Load logo & background
        self.logo = load_image("data/bharat_bhojan_logo.png",(120,120))
        self.bg_image = load_image("data/background.jpg",(1000,700))
        if self.bg_image:
            bg_label = tk.Label(self,image=self.bg_image)
            bg_label.place(relwidth=1, relheight=1)

        # Data
        self.menu_lookup = {}
        self.sales = []
        self.tables = {f"T{i}":"Free" for i in range(1,7)}

        # Initialize DB & menu
        self.ensure_db_and_menu()
        self.load_menu_from_db()
        self.current_user_role = None
        self.build_login()

    # ---------------- Database / Menu ----------------
    def ensure_db_and_menu(self):
        os.makedirs("db", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                itemname TEXT UNIQUE,
                price REAL,
                category TEXT,
                gst REAL DEFAULT 0.05
            )
        """)
        conn.commit()
        if os.path.exists(MENU_CSV):
            with open(MENU_CSV,newline='',encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [(r['itemname'].strip(), float(r['price']), r.get('category','').strip(), float(r.get('gst',0.05))) for r in reader]
                cur.executemany("INSERT OR IGNORE INTO menu(itemname,price,category,gst) VALUES (?,?,?,?)", rows)
                conn.commit()
        conn.close()

    def load_menu_from_db(self):
        self.menu_lookup.clear()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT itemname,price,category,gst FROM menu")
        for item,price,cat,gst in cur.fetchall():
            self.menu_lookup[item] = {"price":price,"category":cat or "Other","gst":gst}
        conn.close()

    # ---------------- Login ----------------
    def build_login(self):
        self.clear_root()
        frm = tk.Frame(self,bg="#eef2ff", padx=20,pady=20)
        frm.place(relx=0.5,rely=0.35,anchor="center")
        if self.logo:
            tk.Label(frm,image=self.logo,bg="#eef2ff").grid(row=0,columnspan=2,pady=10)
        tk.Label(frm,text="Bharat Bhojan", font=("Helvetica",26,"bold"), bg="#eef2ff").grid(row=1,columnspan=2,pady=(0,10))
        tk.Label(frm,text="Username:", bg="#eef2ff").grid(row=2,column=0,sticky="e", padx=5,pady=6)
        tk.Label(frm,text="Password:", bg="#eef2ff").grid(row=3,column=0,sticky="e", padx=5,pady=6)
        self.user_entry = tk.Entry(frm)
        self.pwd_entry = tk.Entry(frm, show="*")
        self.user_entry.grid(row=2,column=1,padx=5,pady=6)
        self.pwd_entry.grid(row=3,column=1,padx=5,pady=6)
        tk.Button(frm,text="Login", bg="#6366f1", fg="white", width=20, command=self.login).grid(row=4,columnspan=2,pady=10)
        tk.Label(frm,text="Demo: Admin/admin • Cashier/cashier", font=("Arial",9), bg="#eef2ff").grid(row=5,columnspan=2)

    def login(self):
        u,p = self.user_entry.get().strip(), self.pwd_entry.get().strip()
        if (u=="admin" and p=="admin") or (u=="cashier" and p=="cashier"):
            self.current_user_role = u.capitalize()
            self.build_main_ui()
        else:
            messagebox.showerror("Login Failed","Invalid credentials")

    # ---------------- Main UI ----------------
    def build_main_ui(self):
        self.clear_root()
        # Header
        header = tk.Frame(self, bg="#0f172a", height=60)
        header.pack(fill="x")
        if self.logo:
            tk.Label(header,image=self.logo,bg="#0f172a").pack(side="left", padx=10)
        tk.Label(header,text=f"Bharat Bhojan — Role: {self.current_user_role}", fg="white", bg="#0f172a", font=("Arial",14)).pack(side="left", padx=12)
        self.clock_lbl = tk.Label(header, fg="white", bg="#0f172a", font=("Arial",12))
        self.clock_lbl.pack(side="right", padx=12)
        self.update_clock()

        # Menu Tree
        left = tk.Frame(self,bg="#f5f5f5")
        left.pack(side="left", fill="y", padx=6, pady=6)
        tk.Label(left,text="Menu", font=("Arial",14,"bold"), bg="#f5f5f5").pack(anchor="w")
        self.menu_tree = ttk.Treeview(left, columns=("price",), show="tree headings", height=24)
        self.menu_tree.heading("#0", text="Item")
        self.menu_tree.heading("price", text="Price")
        self.menu_tree.column("price", width=80, anchor="center")
        self.menu_tree.pack()
        self.populate_menu_tree()
        self.menu_tree.bind("<Double-1>", lambda e: self.add_selected_item())

        # Order & billing frame
        center = tk.Frame(self,bg="#f5f5f5")
        center.pack(side="left", fill="both", expand=True, padx=6,pady=6)
        tk.Label(center,text="Order", font=("Arial",14,"bold"), bg="#f5f5f5").pack(anchor="w")
        self.order_items = {}
        self.order_listbox = tk.Listbox(center, height=20, width=50)
        self.order_listbox.pack(side="left", fill="y")
        sb = tk.Scrollbar(center, orient="vertical", command=self.order_listbox.yview)
        sb.pack(side="left", fill="y")
        self.order_listbox.config(yscrollcommand=sb.set)

        ctrl = tk.Frame(center)
        ctrl.pack(fill="x", pady=6)
        tk.Button(ctrl,text="Add Selected Item", bg="#10b981", fg="white", command=self.add_selected_item).pack(side="left", padx=4)
        tk.Button(ctrl,text="Remove Selected", bg="#ef4444", fg="white", command=self.remove_selected).pack(side="left", padx=4)
        tk.Button(ctrl,text="Load Sample Bills", command=self.load_sample_bills).pack(side="left", padx=4)
        tk.Label(center,text="Discount %:").pack(anchor="w", pady=(10,0))
        self.discount_var = tk.DoubleVar(value=0.0)
        tk.Entry(center,textvariable=self.discount_var,width=8).pack(anchor="w", pady=(0,6))
        tk.Label(center,text="Payment Method:").pack(anchor="w")
        self.pay_method = tk.StringVar(value="cash")
        tk.Radiobutton(center,text="Cash",variable=self.pay_method,value="cash").pack(anchor="w")
        tk.Radiobutton(center,text="UPI",variable=self.pay_method,value="upi").pack(anchor="w")
        tk.Button(center,text="Place Order & Show Bill", bg="#2563eb", fg="white", command=self.place_order).pack(fill="x", pady=6)
        tk.Button(center,text="Share (WhatsApp)", bg="#25D366", fg="white", command=self.share_whatsapp).pack(fill="x", pady=3)
        tk.Button(center,text="Share (Email)", bg="#3b82f6", fg="white", command=self.share_email).pack(fill="x", pady=3)
        tk.Button(center,text="Export Sales Report", command=self.export_sales_csv).pack(fill="x", pady=6)

        # Table management
        tbl_frame = tk.Frame(self, pady=6)
        tbl_frame.pack(fill="x")
        tk.Label(tbl_frame,text="Table Management (Dine-in)", font=("Arial",12,"bold")).pack(side="left", padx=6)
        self.table_buttons = {}
        for t in self.tables:
            b = tk.Button(tbl_frame,text=f"{t}\n{self.tables[t]}", width=8,height=2, command=lambda tt=t: self.toggle_table(tt))
            b.pack(side="left", padx=4)
            self.table_buttons[t] = b
        self.update_table_buttons()

    # ---------------- Menu ----------------
    def populate_menu_tree(self):
        by_cat = {}
        for item,v in self.menu_lookup.items():
            cat = v.get("category") or "Other"
            by_cat.setdefault(cat,[]).append((item,v['price']))
        for cat,items in sorted(by_cat.items()):
            node = self.menu_tree.insert("", "end", text=cat, open=True)
            for it, price in sorted(items):
                self.menu_tree.insert(node,"end", text=it, values=(f"₹{price:.2f}",))

    # ---------------- Utilities ----------------
    def clear_root(self):
        for w in self.winfo_children(): w.destroy()
    def update_clock(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self,"clock_lbl"): self.clock_lbl.config(text=now)
        self.after(1000,self.update_clock)

    # ---------------- Orders ----------------
    def add_selected_item(self):
        sel = self.menu_tree.selection()
        if not sel: 
            messagebox.showwarning("Select Item","Please select a menu item, not category")
            return
        for s in sel:
            if self.menu_tree.parent(s)=="": 
                messagebox.showwarning("Select Item","Please select an actual item, not category")
                return
            item = self.menu_tree.item(s,"text")
            qty = self.ask_quantity(item)
            if qty and qty>0:
                self.order_items[item] = self.order_items.get(item,0)+qty
        self.refresh_order_list()

    def ask_quantity(self,item):
        qwin = tk.Toplevel(self)
        qwin.title("Quantity")
        qwin.transient(self)
        tk.Label(qwin,text=f"Quantity for {item}:").pack(padx=10,pady=6)
        var = tk.IntVar(value=1)
        tk.Entry(qwin,textvariable=var).pack(padx=10,pady=6)
        result = {"val":None}
        def ok():
            try:
                v = int(var.get())
                if v<0: raise ValueError()
                result["val"] = v
                qwin.destroy()
            except:
                messagebox.showerror("Invalid","Enter non-negative integer")
        tk.Button(qwin,text="OK",command=ok).pack(pady=6)
        qwin.grab_set()
        self.wait_window(qwin)
        return result["val"] or 0

    def refresh_order_list(self):
        self.order_listbox.delete(0,tk.END)
        for it,q in self.order_items.items():
            p = self.menu_lookup[it]['price']*q
            self.order_listbox.insert(tk.END,f"{it} x{q} = ₹{p:.2f}")

    def remove_selected(self):
        sel = self.order_listbox.curselection()
        if not sel: return
        item_text = self.order_listbox.get(sel[0])
        itemname = item_text.split(" x")[0]
        if itemname in self.order_items:
            del self.order_items[itemname]
        self.refresh_order_list()

    # ---------------- Billing ----------------
    def compute_bill(self, items_with_qty, discount_percent=0.0):
        subtotal = 0.0
        gst_total = 0.0
        itemized = {}
        for item,qty in items_with_qty.items():
            price = self.menu_lookup[item]['price']
            gst_rate = self.menu_lookup[item].get('gst',0.05)
            amt = price*qty
            gst_amt = amt*gst_rate
            itemized[item] = {"qty":qty,"price":price,"amount":round(amt,2),"gst":round(gst_amt,2)}
            subtotal += amt
            gst_total += gst_amt
        discount = subtotal*(discount_percent/100)
        taxable = subtotal-discount
        if subtotal>0:
            gst_total = gst_total*(taxable/subtotal)
        total = taxable+gst_total
        return {"itemized":itemized,"subtotal":round(subtotal,2),"discount":round(discount,2),
                "gst_total":round(gst_total,2),"total":round(total,2)}

    # ---------------- Dine-in Table Feature ----------------
    def toggle_table(self, table_name):
        status = self.tables[table_name]
        if status=="Free":
            self.tables[table_name]="Occupied"
        else:
            self.tables[table_name]="Free"
        self.update_table_buttons()

    def update_table_buttons(self):
        for t, b in self.table_buttons.items():
            status = self.tables[t]
            b.config(text=f"{t}\n{status}")
            if status=="Occupied": b.config(bg="#fb923c")
            elif status=="Free": b.config(bg="#10b981")
            else: b.config(bg="SystemButtonFace")

    def place_order(self):
        if not self.order_items:
            messagebox.showwarning("No Selection","Please select at least one item.")
            return

        is_dine_in = messagebox.askyesno("Order Type","Is this a Dine-in order?")
        table = None
        if is_dine_in:
            free_tables = [t for t,s in self.tables.items() if s=="Free"]
            if not free_tables:
                messagebox.showwarning("No Free Tables","All tables are occupied!")
                return
            table = free_tables[0]
            self.tables[table] = "Occupied"
            self.update_table_buttons()

        discount = float(self.discount_var.get() or 0.0)
        bill = self.compute_bill(self.order_items, discount)
        bill_text = self.format_bill_text(bill, table)
        self.show_bill_window(bill_text, bill)

        sale = {
            "datetime": datetime.datetime.now().isoformat(),
            "table": table or "",
            "items": self.order_items.copy(),
            "subtotal": bill['subtotal'],
            "discount": bill['discount'],
            "gst": bill['gst_total'],
            "total": bill['total'],
            "payment": self.pay_method.get()
        }
        self.append_sale_csv(sale)
        self.sales.append(sale)
        self.order_items = {}
        self.refresh_order_list()
        self.discount_var.set(0.0)

    def format_bill_text(self,bill,table=None):
        lines = []
        lines.append("🍴 Bharat Bhojan 🍴")
        lines.append(f"Date: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
        if table: lines.append(f"Table: {table}")
        lines.append("-"*40)
        lines.append(f"{'Item':20}Qty   Amount")
        for it,d in bill['itemized'].items():
            lines.append(f"{it:20} x{d['qty']:<3} = ₹{d['amount']:.2f}")
        lines.append("-"*40)
        lines.append(f"Subtotal         : ₹{bill['subtotal']:.2f}")
        lines.append(f"Discount         : -₹{bill['discount']:.2f}")
        lines.append(f"GST              : ₹{bill['gst_total']:.2f}")
        lines.append(f"Total            : ₹{bill['total']:.2f}")
        lines.append(f"Payment Method   : {self.pay_method.get().upper()}")
        if self.pay_method.get()=="upi":
            lines.append(f"UPI Link: {self.make_upi_link(bill['total'])}")
        lines.append("-"*40)
        lines.append("Thank you! Visit again 🙂")
        return "\n".join(lines)

    def show_bill_window(self,text,bill):
        w = tk.Toplevel(self)
        w.title("Bill")
        txt = tk.Text(w,width=60,height=28)
        txt.pack(padx=8,pady=8)
        txt.insert("end",text)
        txt.config(state="disabled")
        btnf = tk.Frame(w)
        btnf.pack()
        if self.pay_method.get()=="upi":
            tk.Button(btnf,text="Open UPI", bg="#7c3aed", fg="white", command=lambda:webbrowser.open(self.make_upi_link(bill['total']))).pack(side="left", padx=4)
        tk.Button(btnf,text="Save Bill (txt)", command=lambda:self.save_bill_text(text)).pack(side="left", padx=4)
        tk.Button(btnf,text="Close", command=w.destroy).pack(side="left", padx=4)

    def make_upi_link(self,amount):
        am = f"{amount:.2f}"
        return f"upi://pay?pa={quote_plus(UPI_ID)}&pn={quote_plus(UPI_NAME)}&am={am}&cu=INR"

    def save_bill_text(self,text):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file","*.txt")])
        if path:
            with open(path,"w",encoding="utf-8") as f: f.write(text)
            messagebox.showinfo("Saved",f"Bill saved at {path}")

    def share_whatsapp(self):
        if not self.sales: return
        last = self.sales[-1]
        msg = f"Bill Total: ₹{last['total']:.2f}\nThank you!"
        url = f"https://wa.me/?text={quote_plus(msg)}"
        webbrowser.open(url)

    def share_email(self):
        if not self.sales: return
        last = self.sales[-1]
        subject = quote_plus("Your Bharat Bhojan Bill")
        body = quote_plus(f"Thank you for visiting! Your bill total: ₹{last['total']:.2f}")
        webbrowser.open(f"mailto:?subject={subject}&body={body}")

    def append_sale_csv(self,sale):
        write_header = not os.path.exists(SALES_CSV)
        with open(SALES_CSV,"a",newline="",encoding="utf-8") as f:
            writer = csv.DictWriter(f,fieldnames=sale.keys())
            if write_header: writer.writeheader()
            writer.writerow(sale)

    def export_sales_csv(self):
        if not self.sales:
            messagebox.showwarning("No Sales","No sales to export")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if path:
            keys = self.sales[0].keys()
            with open(path,"w",newline="",encoding="utf-8") as f:
                writer = csv.DictWriter(f,fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.sales)
            messagebox.showinfo("Exported",f"Sales exported to {path}")

    # ---------------- Sample Bills ----------------
    def load_sample_bills(self):
        if not os.path.exists(SAMPLE_JSON):
            messagebox.showwarning("Missing",f"No sample file found: {SAMPLE_JSON}")
            return
        with open(SAMPLE_JSON,"r",encoding="utf-8") as f:
            data = json.load(f)
        for b in data:
            self.order_items = b.get("items",{})
            self.refresh_order_list()
            self.discount_var.set(b.get("discount",0.0))
            self.pay_method.set(b.get("payment","cash"))

if __name__=="__main__":
    app = RestaurantBillingApp()
    app.mainloop()
