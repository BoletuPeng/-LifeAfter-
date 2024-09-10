import json
import os
from typing import List, Dict, Any, Tuple
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D
import copy
import matplotlib.pyplot as plt
import math


plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

def sort_items(items):
    category_order = {
        "木材": 0,
        "矿物": 1,
        "麻料": 2,
        "怪物": 3,
        "其它": 4,
        "半成品": 5
    }

    def sort_key(item):
        name, data = item
        category_rank = category_order.get(data['category'], len(category_order))
        return (
            category_rank,
            data['quality'],
            data['level'],
            name
        )
    
    return sorted(items.items(), key=sort_key)

def sort_items_for_recipe(items):
    sorted_items = sort_items(items)
    non_crafted = [(name, data) for name, data in sorted_items if data['category'] != '半成品']
    crafted = [(name, data) for name, data in sorted_items if data['category'] == '半成品']
    return non_crafted + crafted

class DataManager:
    def __init__(self):
        self.config_file = "config.json"
        self.load_config()
        self.temp_prices_filename = "temp_prices.json"
        self.load_data()
        self.load_temp_prices()
        self.use_custom_prices = False

    def get_base_materials_data(self):
        """
        获取基础材料的属性数据（深拷贝）
        """
        return copy.deepcopy(self.data["items"])
    
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.filename = config.get('data_file', "crafting_data.json")
        else:
            self.filename = "crafting_data.json"

    def save_config(self):
        config = {'data_file': self.filename}
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def load_data(self, file_path=None):
        if file_path:
            self.filename = file_path
            self.save_config()  # Save the new file path to config
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {"items": {}, "recipes": {}, "last_item": None}

        # Ensure all items have a ticket_price field
        for item in self.data["items"].values():
            if "ticket_price" not in item:
                item["ticket_price"] = -1
            if "camp_contribution" not in item:
                item["camp_contribution"] = -1
            if "new_dollar" not in item:
                item["new_dollar"] = -1

        # Ensure all recipes have the new fields
        for recipe in self.data["recipes"].values():
            if "crafting_level" not in recipe:
                recipe["crafting_level"] = 0
            if "recipe_type" not in recipe:
                recipe["recipe_type"] = "未设定"
            if "is_exclusive" not in recipe:
                recipe["is_exclusive"] = False

    def load_temp_prices(self):
        if os.path.exists(self.temp_prices_filename):
            with open(self.temp_prices_filename, 'r') as f:
                self.temp_prices = json.load(f)
        else:
            self.temp_prices = {}

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=2)

    def save_temp_prices(self):
        with open(self.temp_prices_filename, 'w') as f:
            json.dump(self.temp_prices, f, indent=2)

    def get_item_price(self, item_name):
        if self.use_custom_prices and item_name in self.temp_prices:
            return self.temp_prices[item_name]
        return self.data["items"][item_name]["price"]

    def set_temp_price(self, item_name, price):
        self.temp_prices[item_name] = price
        self.save_temp_prices()
    
    def clear_temp_prices(self):
        self.temp_prices.clear()
        self.save_temp_prices()

    def set_use_custom_prices(self, use_custom):
        self.use_custom_prices = use_custom

    def get_custom_price_changes(self):
        changes = []
        for item_name, custom_price in self.temp_prices.items():
            original_price = self.data["items"][item_name]["price"]
            changes.append((item_name, original_price, custom_price))
        return changes

    def add_item(self, name: str, price: float, category: str, level: int, quality: int, ticket_price: float, camp_contribution: float, new_dollar: float):
        self.data["items"][name] = {
            "price": price,
            "category": category,
            "level": level,
            "quality": quality,
            "ticket_price": ticket_price if ticket_price is not None else -1,
            "camp_contribution": camp_contribution if camp_contribution is not None else -1,
            "new_dollar": new_dollar if new_dollar is not None else -1
        }
        self.save_data()

    def add_recipe(self, product: str, materials: List[Dict[str, Any]], quantity: int, 
                   crafting_level: int, recipe_type: str, is_exclusive: bool):
        self.data["recipes"][product] = {
            "materials": materials,
            "quantity": quantity,
            "crafting_level": crafting_level,
            "recipe_type": recipe_type,
            "is_exclusive": is_exclusive
        }
        self.save_data()

    def get_items(self) -> Dict[str, Dict[str, Any]]:
        return self.data["items"]

    def get_recipes(self) -> Dict[str, Dict[str, Any]]:
        return self.data["recipes"]

    def set_last_item(self, item_data: Dict[str, Any]):
        self.data["last_item"] = item_data
        self.save_data()

    def get_last_item(self) -> Dict[str, Any]:
        return self.data.get("last_item")

    def update_item(self, name: str, price: float, category: str, level: int, quality: int, ticket_price: float, camp_contribution: float, new_dollar: float):
        if name in self.data["items"]:
            self.data["items"][name] = {
                "price": price,
                "category": category,
                "level": level,
                "quality": quality,
                "ticket_price": ticket_price if ticket_price is not None else -1,
                "camp_contribution": camp_contribution if camp_contribution is not None else -1,
                "new_dollar": new_dollar if new_dollar is not None else -1
            }
            self.save_data()
        else:
            raise KeyError(f"Item '{name}' not found in the database.")
        
    def delete_item(self, name: str):
        if name in self.data["items"]:
            del self.data["items"][name]
            self.save_data()
        else:
            raise KeyError(f"Item '{name}' not found in the database.")

    def update_recipe(self, product: str, materials: List[Dict[str, Any]], quantity: int, 
                      crafting_level: int, recipe_type: str, is_exclusive: bool):
        if product in self.data["recipes"]:
            self.data["recipes"][product] = {
                "materials": materials,
                "quantity": quantity,
                "crafting_level": crafting_level,
                "recipe_type": recipe_type,
                "is_exclusive": is_exclusive
            }
            self.save_data()
        else:
            raise KeyError(f"Recipe for '{product}' not found in the database.")

    def delete_recipe(self, product: str):
        if product in self.data["recipes"]:
            del self.data["recipes"][product]
            self.save_data()
        else:
            raise KeyError(f"Recipe for '{product}' not found in the database.")
    
    def get_sorted_items(self) -> List[Tuple[str, Dict[str, Any]]]:
        return sort_items(self.data["items"])

    def get_sorted_items_for_recipe(self) -> List[Tuple[str, Dict[str, Any]]]:
        return sort_items_for_recipe(self.data["items"])
    
    def get_sorted_base_items(self):
        base_items = {name: data for name, data in self.data["items"].items() if name not in self.data["recipes"]}
        return sort_items(base_items)
    
    def get_all_categories(self) -> List[str]:
        predefined_categories = ["木材", "矿物", "麻料", "怪物", "其它", "半成品"]
        existing_categories = set(data['category'] for _, data in self.get_sorted_items())
        return sorted(set(predefined_categories) | existing_categories)
    
    def filter_materials(self, value: str) -> List[str]:
        sorted_items = self.get_sorted_items_for_recipe()
        materials = [name for name, _ in sorted_items] + list(self.get_recipes().keys())
        filtered_materials = [m for m in materials if value.lower() in m.lower()]
        return filtered_materials
    
    def get_recipe_tree(self, item_name: str, quantity: float = 1, level: int = 0) -> Dict[str, Any]:
        recipes = self.get_recipes()
        items = self.get_items()
        
        if item_name in recipes:
            recipe = recipes[item_name]
            children = []
            total_cost = 0
            for material in recipe["materials"]:
                material_name = material["name"]
                material_quantity = material["quantity"] * quantity / recipe["quantity"]
                child = self.get_recipe_tree(material_name, material_quantity, level + 1)
                children.append(child)
                total_cost += child["total_cost"]
            
            return {
                "name": item_name,
                "quantity": quantity,
                "level": level,
                "is_recipe": True,
                "children": children,
                "total_cost": total_cost,
                "unit_cost": total_cost / quantity
            }
        elif item_name in items:
            price = self.get_item_price(item_name)
            total_cost = price * quantity
            return {
                "name": item_name,
                "quantity": quantity,
                "level": level,
                "is_recipe": False,
                "children": [],
                "price": price,
                "total_cost": total_cost,
                "unit_cost": price
            }
        else:
            raise ValueError(f"Item not found: {item_name}")
    
    @staticmethod
    def round_quantity(quantity, threshold=1e-4):
        """
        对数量进行舍入，考虑到非常接近整数的浮点数。
        
        如果数量与其最接近的整数的差小于阈值，则舍入到该整数。
        否则，向上取整。
        """
        rounded = round(quantity)
        if abs(quantity - rounded) < threshold:
            return int(rounded)
        else:
            return math.ceil(quantity)



class CraftingPage(ttk.Frame):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.create_widgets()
        self.tree_items = {}  # 用于存储树形项目的引用

    def populate_recipe_tree(self, recipe_data, parent=""):
        item_id = self.recipe_tree.insert(parent, "end", text=self.format_item_name(recipe_data),
                                        values=self.format_item_values(recipe_data),
                                        open=False)
        
        if recipe_data["is_recipe"]:
            self.recipe_tree.item(item_id, tags=("recipe",))
            for child in recipe_data["children"]:
                self.populate_recipe_tree(child, item_id)
        else:
            self.recipe_tree.item(item_id, tags=("material",))
        
        return item_id

    def format_item_name(self, item):
        indent = "  " * item["level"]
        prefix = "├─ " if item["level"] > 0 else ""
        return f"{indent}{prefix}{item['name']}"

    def format_item_values(self, item):
        quantity = f"{item['quantity']:.2f}"
        if item["is_recipe"]:
            unit_cost = f"{item['unit_cost']:.2f}" if 'unit_cost' in item else ""
            total_cost = f"{item['total_cost']:.2f}"
        else:
            unit_cost = f"{item['price']:.2f}"
            total_cost = f"{item['total_cost']:.2f}"
        return (quantity, unit_cost, total_cost)
    
    def create_widgets(self):

        # 物品选择下拉菜单
        row = 0
        tk.Label(self, text="选择物品:").grid(row=row, column=0, pady=5, padx=5, sticky="w")
        self.item_var = tk.StringVar()
        self.item_dropdown = ttk.Combobox(self, textvariable=self.item_var)
        self.item_dropdown.grid(row=row, column=1, pady=5, padx=5, sticky="w")
        self.item_dropdown.bind('<<ComboboxSelected>>', self.update_info)

        
        # 制作路线显示
        row += 1 # row = 1
        tk.Label(self, text="制作路线:").grid(row=row, column=0, pady=5, padx=5, sticky="nw")
        self.recipe_tree = ttk.Treeview(self, columns=("数量", "单价", "总价"), show="tree headings")
        self.recipe_tree.heading("数量", text="数量")
        self.recipe_tree.heading("单价", text="单价 (金条)")
        self.recipe_tree.heading("总价", text="总价 (金条)")
        self.recipe_tree.column("数量", width=50)
        self.recipe_tree.column("单价", width=100)
        self.recipe_tree.column("总价", width=100)
        self.recipe_tree.grid(row=row, column=1, pady=5, padx=5, sticky="nsew")
        self.recipe_tree.bind("<Double-1>", self.on_item_double_click)

        # 滚动条
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.recipe_tree.yview)
        scrollbar.grid(row=row, column=2, sticky="ns")
        self.recipe_tree.configure(yscrollcommand=scrollbar.set)

        # 总成本显示
        row += 1 # row = 2
        self.cost_label = tk.Label(self, text="总制作成本: 0 金条")
        self.cost_label.grid(row=row, column=1, pady=5, padx=5, sticky="w")

        # 复选框
        row += 1 # row = 3
        self.use_custom_prices_var = tk.BooleanVar(value=False)
        self.use_custom_prices_check = ttk.Checkbutton(
            self, 
            text="使用自定义价格预设而非最高价", 
            variable=self.use_custom_prices_var,
            command=self.toggle_custom_prices
        )
        self.use_custom_prices_check.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="w")

        # 添加查看自定义价格按钮
        row += 1 # row = 4
        self.view_custom_prices_button = ttk.Button(
            self, 
            text="查看自定义价格", 
            command=self.view_custom_prices
        )
        self.view_custom_prices_button.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="w")


        # 配置网格权重
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 初始化物品列表
        self.update_item_list()
        
        self.recipe_tree.tag_configure("recipe", background="#E6F3FF")
        self.recipe_tree.tag_configure("material", background="#FFFFFF")

    def update_item_list(self):
        items = list(self.data_manager.get_recipes().keys())
        self.item_dropdown['values'] = items

    def update_info(self, event=None):
        selected_item = self.item_var.get()
        self.recipe_tree.delete(*self.recipe_tree.get_children())
        if selected_item:
            try:
                recipe_data = self.data_manager.get_recipe_tree(selected_item)
                self.populate_recipe_tree(recipe_data)
                
                total_cost = recipe_data['total_cost']
                if self.data_manager.use_custom_prices:
                    cost_label = f"总制作成本: {total_cost:.2f} 金条 (使用自定义价格)"
                else:
                    cost_label = f"总制作成本: {total_cost:.2f} 金条"
                
                self.cost_label.config(text=cost_label)
                
                # 更新自定义价格复选框状态
                self.use_custom_prices_var.set(self.data_manager.use_custom_prices)
                
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                self.cost_label.config(text="总制作成本: N/A")
        else:
            self.cost_label.config(text="总制作成本: 0 金条")
            
            
    def format_item_name(self, item):
        indent = "  " * item["level"]
        prefix = "├─ " if item["level"] > 0 else ""
        return f"{indent}{prefix}{item['name']}"

    def on_item_double_click(self, event):
        item = self.recipe_tree.selection()[0]
        item_text = self.recipe_tree.item(item, "text")
        item_name = item_text.strip().strip("├─ ")
        
        if item_name in self.data_manager.get_items():
            self.update_temp_price(item_name)


    def update_temp_price(self, item_name):
        current_price = self.data_manager.get_item_price(item_name)
        new_price = simpledialog.askfloat("更新临时价格", f"输入 {item_name} 的新价格:", initialvalue=current_price)
        if new_price is not None:
            self.data_manager.set_temp_price(item_name, new_price)
            self.update_info()

    def toggle_custom_prices(self):
        use_custom = self.use_custom_prices_var.get()
        self.data_manager.set_use_custom_prices(use_custom)
        self.update_info()

    def view_custom_prices(self):
        changes = self.data_manager.get_custom_price_changes()
        if not changes:
            messagebox.showinfo("自定义价格", "当前没有自定义价格")
        else:
            custom_prices_window = tk.Toplevel(self)
            custom_prices_window.title("自定义价格列表")
            
            tree = ttk.Treeview(custom_prices_window, columns=("原价", "自定义价格"), show="headings")
            tree.heading("原价", text="原价")
            tree.heading("自定义价格", text="自定义价格")
            
            for item_name, original_price, custom_price in changes:
                tree.insert("", "end", text=item_name, values=(f"{original_price:.2f}", f"{custom_price:.2f}"))
            
            tree.pack(expand=True, fill="both")

    def reset_prices(self):
        # 重置所有物品价格为原始参考价格
        items = self.data_manager.get_items()
        for name, item in items.items():
            if "reference_price" in item:
                self.data_manager.update_item(name, item["reference_price"], item["category"],
                                              item["level"], item["quality"])
        messagebox.showinfo("价格重置", "所有物品价格已重置为参考价格。")
        self.update_info()

class AddItemDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, item_to_edit=None, default_name=None, callback=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.item_to_edit = item_to_edit
        self.default_name = default_name
        self.callback = callback
        self.title("添加新物品" if not item_to_edit else f"编辑物品: {item_to_edit}")
        self.result = None
        self.create_widgets()

    def create_widgets(self):

        # 物品名称
        row = 0
        ttk.Label(self, text="物品名称:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=row, column=1, padx=5, pady=5)

        # 使用金条价格复选框
        row += 1 # row = 1
        self.use_gold_price_var = tk.BooleanVar(value=True)
        self.use_gold_price_check = ttk.Checkbutton(
            self, 
            text="使用金条价格", 
            variable=self.use_gold_price_var,
            command=self.toggle_gold_price_entry
        )
        self.use_gold_price_check.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="w")

        # 物品价格
        row += 1 # row = 2
        ttk.Label(self, text="价格:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.price_entry = ttk.Entry(self)
        self.price_entry.grid(row=row, column=1, padx=5, pady=5)

        # 采集券价格复选框
        row += 1 # row = 3
        self.use_ticket_price_var = tk.BooleanVar(value=False)
        self.use_ticket_price_check = ttk.Checkbutton(
            self, 
            text="使用采集券价格", 
            variable=self.use_ticket_price_var,
            command=self.toggle_ticket_price_entry
        )
        self.use_ticket_price_check.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="w")
        
        # 采集券价格输入框
        row += 1 # row = 4
        ttk.Label(self, text="采集券价格:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.ticket_price_entry = ttk.Entry(self, state="disabled")
        self.ticket_price_entry.grid(row=row, column=1, padx=5, pady=5)

        # 使用营地价格复选框
        row += 1
        self.use_camp_price_var = tk.BooleanVar(value=False)
        self.use_camp_price_check = ttk.Checkbutton(
            self, 
            text="使用营地价格", 
            variable=self.use_camp_price_var,
            command=self.toggle_camp_price_entry
        )
        self.use_camp_price_check.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="w")
        
        # 贡献点价格输入框
        row += 1
        ttk.Label(self, text="贡献点价格:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.camp_contribution_entry = ttk.Entry(self, state="disabled")
        self.camp_contribution_entry.grid(row=row, column=1, padx=5, pady=5)

        # 新币价格输入框
        row += 1
        ttk.Label(self, text="新币价格:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.new_dollar_entry = ttk.Entry(self, state="disabled")
        self.new_dollar_entry.grid(row=row, column=1, padx=5, pady=5)

        # 物品类别
        row += 1 # row = 8
        ttk.Label(self, text="类别:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        all_categories = self.data_manager.get_all_categories()
        self.category_combobox = ttk.Combobox(self, values=all_categories)
        self.category_combobox.grid(row=row, column=1, padx=5, pady=5)

        # 物品等级
        row += 1 # row = 9
        ttk.Label(self, text="等级 (1-14):").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.level_combobox = ttk.Combobox(self, values=list(range(1, 15)))
        self.level_combobox.grid(row=row, column=1, padx=5, pady=5)

        # 物品品质
        row += 1 # row = 10
        ttk.Label(self, text="品质 (1-5):").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.quality_combobox = ttk.Combobox(self, values=list(range(1, 6)))
        self.quality_combobox.grid(row=row, column=1, padx=5, pady=5)

        # 添加/更新按钮
        row += 1 # row = 11
        self.add_button = ttk.Button(self, text="添加" if not self.item_to_edit else "更新", command=self.add_or_update_item)
        self.add_button.grid(row=row, column=0, columnspan=2, pady=10)

        # 删除按钮（仅在编辑模式下显示）
        row += 1 # row = 12
        if self.item_to_edit:
            self.delete_button = ttk.Button(self, text="删除", command=self.delete_item, style="Danger.TButton")
            self.delete_button.grid(row=row, column=0, columnspan=2, pady=10)

        self.load_default_values()
        self.bind_enter_key()

    def bind_enter_key(self):
        # 为所有Entry和Combobox绑定回车键处理函数
        self.name_entry.bind("<Return>", self.handle_enter)
        self.price_entry.bind("<Return>", self.handle_enter)
        self.ticket_price_entry.bind("<Return>", self.handle_enter)
        self.category_combobox.bind("<Return>", self.handle_enter)
        self.level_combobox.bind("<Return>", self.handle_enter)
        self.quality_combobox.bind("<Return>", self.handle_enter)
    
    def handle_enter(self, event):
        # 阻止回车键的默认行为
        return "break"

    def toggle_gold_price_entry(self):
        if self.use_gold_price_var.get():
            self.price_entry.config(state="normal")
        else:
            self.price_entry.config(state="disabled")

    def toggle_ticket_price_entry(self):
        if self.use_ticket_price_var.get():
            self.ticket_price_entry.config(state="normal")
        else:
            self.ticket_price_entry.config(state="disabled")

    def toggle_camp_price_entry(self):
        if self.use_camp_price_var.get():
            self.camp_contribution_entry.config(state="normal")
            self.new_dollar_entry.config(state="normal")
        else:
            self.camp_contribution_entry.config(state="disabled")
            self.new_dollar_entry.config(state="disabled")

    def load_default_values(self):
        if self.item_to_edit:
            item_data = self.data_manager.get_items()[self.item_to_edit]
            self.name_entry.insert(0, self.item_to_edit)
            if item_data['price'] != -1:
                self.price_entry.insert(0, str(item_data['price']))
            else:
                self.use_gold_price_var.set(False)
                self.price_entry.config(state="disabled")

            if item_data['camp_contribution'] != -1 and item_data['new_dollar'] != -1:
                self.use_camp_price_var.set(True)
                self.camp_contribution_entry.config(state="normal")
                self.new_dollar_entry.config(state="normal")
                self.camp_contribution_entry.insert(0, str(item_data['camp_contribution']))
                self.new_dollar_entry.insert(0, str(item_data['new_dollar']))
            self.toggle_camp_price_entry()

            self.category_combobox.set(item_data['category'])
            self.level_combobox.set(str(item_data['level']))
            self.quality_combobox.set(str(item_data['quality']))
            if item_data['ticket_price'] != -1:
                self.use_ticket_price_var.set(True)
                self.ticket_price_entry.config(state="normal")
                self.ticket_price_entry.insert(0, str(item_data['ticket_price']))
            self.toggle_gold_price_entry()
            self.toggle_ticket_price_entry()

        elif self.default_name:
            self.name_entry.insert(0, self.default_name)
            last_item = self.data_manager.get_last_item()
            if last_item:
                self.category_combobox.set(last_item['category'])
                self.level_combobox.set(str(last_item['level']))
                self.quality_combobox.set(str(last_item['quality']))
            else:
                # 设置默认值
                self.category_combobox.set("木材")
                self.level_combobox.set("1")
                self.quality_combobox.set("1")
        else:
            last_item = self.data_manager.get_last_item()
            if last_item:
                self.category_combobox.set(last_item['category'])
                self.level_combobox.set(str(last_item['level']))
                self.quality_combobox.set(str(last_item['quality']))
            else:
                # 设置默认值
                self.category_combobox.set("木材")
                self.level_combobox.set("1")
                self.quality_combobox.set("1")

    def add_or_update_item(self):
        name = self.name_entry.get()
        try:
            price = float(self.price_entry.get()) if self.use_gold_price_var.get() else -1
            category = self.category_combobox.get()
            level = int(self.level_combobox.get())
            quality = int(self.quality_combobox.get())

            if self.use_ticket_price_var.get():
                ticket_price = float(self.ticket_price_entry.get())
            else:
                ticket_price = -1

            if self.use_camp_price_var.get():
                camp_contribution = float(self.camp_contribution_entry.get())
                new_dollar = float(self.new_dollar_entry.get())
            else:
                camp_contribution = -1
                new_dollar = -1

            if not name or not category or level not in range(1, 15) or quality not in range(1, 6):
                raise ValueError

            new_item_data = {
                "price": price,
                "category": category,
                "level": level,
                "quality": quality,
                "ticket_price": ticket_price,
                "camp_contribution": camp_contribution,
                "new_dollar": new_dollar
            }

            if self.item_to_edit:
                if name != self.item_to_edit:
                    self.data_manager.delete_item(self.item_to_edit)
                self.data_manager.update_item(name, price, category, level, quality, ticket_price, camp_contribution, new_dollar)
                messagebox.showinfo("成功", f"{name} 已更新")
            else:
                self.data_manager.add_item(name, price, category, level, quality, ticket_price, camp_contribution, new_dollar)
                self.data_manager.set_last_item(new_item_data)
                messagebox.showinfo("成功", f"{name} 已添加到数据库")

            self.result = name
            if self.callback:
                self.callback(name)
            self.destroy()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的信息")

    def delete_item(self):
        if messagebox.askyesno("确认删除", f"您确定要删除物品 '{self.item_to_edit}' 吗？"):
            try:
                self.data_manager.delete_item(self.item_to_edit)
                messagebox.showinfo("成功", f"物品 '{self.item_to_edit}' 已被删除")
                self.destroy()
            except KeyError as e:
                messagebox.showerror("错误", str(e))

class RecipeDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, new_recipe=True, recipe_name=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.new_recipe = new_recipe
        self.recipe_name = recipe_name
        self.result = None
        self.title("添加新配方" if new_recipe else f"编辑配方: {recipe_name}")
        self.material_entries = []
        self.create_widgets()

    def create_widgets(self):
        # 配方名称
        row = 0
        ttk.Label(self, text="配方名称:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.name_var = tk.StringVar(value=self.recipe_name if self.recipe_name else "")
        self.name_entry = ttk.Entry(self, textvariable=self.name_var)
        self.name_entry.grid(row=row, column=1, padx=5, pady=5, columnspan=2)

        # 材料选择
        row += 1 # row = 1
        self.materials_frame = ttk.Frame(self)
        self.materials_frame.grid(row=row, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        self.add_material_entry()

        # 添加材料按钮
        row += 1 # row = 2
        ttk.Button(self, text="添加材料", command=self.add_material_entry).grid(row=row, column=0, columnspan=3, pady=5)

        # 产品数量
        row += 1 # row = 3
        ttk.Label(self, text="产品数量:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.product_quantity_var = tk.IntVar(value=1)
        ttk.Entry(self, textvariable=self.product_quantity_var).grid(row=row, column=1, padx=5, pady=5)

        # 制作等级
        row += 1 # row = 4
        ttk.Label(self, text="制作等级 (1-150):").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.crafting_level_var = tk.IntVar(value=1)
        self.crafting_level_combobox = ttk.Combobox(self, textvariable=self.crafting_level_var, values=list(range(1, 151)))
        self.crafting_level_combobox.grid(row=row, column=1, padx=5, pady=5)

        # 配方类型
        row += 1 # row = 5
        ttk.Label(self, text="配方类型:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.recipe_type_var = tk.StringVar(value="其它")
        self.recipe_type_combobox = ttk.Combobox(self, textvariable=self.recipe_type_var, values=["家具", "武器", "护甲", "其它"])
        self.recipe_type_combobox.grid(row=row, column=1, padx=5, pady=5)

        # 是否专属
        row += 1 # row = 6
        self.is_exclusive_var = tk.BooleanVar(value=False)
        self.is_exclusive_check = ttk.Checkbutton(self, text="是否专属", variable=self.is_exclusive_var)
        self.is_exclusive_check.grid(row=row, column=0, columnspan=2, pady=5, padx=5, sticky="w")

        # 保存按钮
        row += 1 # row = 7
        ttk.Button(self, text="保存", command=self.save_recipe).grid(row=row, column=0, columnspan=3, pady=10)

        # 只在编辑现有配方时显示删除按钮
        row += 1 # row = 8
        if not self.new_recipe:
            ttk.Button(self, text="删除配方", command=self.delete_recipe, style="Danger.TButton").grid(row=row, column=2, pady=10, padx=5)
            self.load_recipe_data()
        self.bind_enter_key()

    def bind_enter_key(self):
        # 为所有Entry和Combobox绑定回车键处理函数
        self.name_entry.bind("<Return>", self.handle_enter)
        self.product_quantity_var.trace_add("write", lambda *args: self.handle_enter(None))
        self.crafting_level_combobox.bind("<Return>", self.handle_enter)
        self.recipe_type_combobox.bind("<Return>", self.handle_enter)

        # 为材料输入框绑定回车键处理函数
        for entry in self.material_entries:
            entry['combobox'].bind("<Return>", self.handle_enter)
            entry['quantity_var'].trace_add("write", lambda *args: self.handle_enter(None))

    def handle_enter(self, event):
        # 阻止回车键的默认行为
        return "break"

    def add_material_entry(self):
        index = len(self.material_entries)
        frame = ttk.Frame(self.materials_frame)
        frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(frame, text=f"材料 {index+1}:").pack(side="left", padx=(0, 5))
        
        var = tk.StringVar()
        combobox = ttk.Combobox(frame, textvariable=var)
        combobox.pack(side="left", padx=5, expand=True, fill="x")
        
        quantity_var = tk.IntVar(value=1)
        quantity_entry = ttk.Entry(frame, textvariable=quantity_var, width=5)
        quantity_entry.pack(side="left", padx=5)
        
        remove_button = ttk.Button(frame, text="X", width=2, command=lambda: self.remove_material_entry(index))
        remove_button.pack(side="left", padx=5)

        self.material_entries.append({
            "frame": frame,
            "var": var,
            "combobox": combobox,
            "quantity_var": quantity_var
        })

        self.update_material_list(combobox)
        combobox.bind("<KeyRelease>", lambda event, cb=combobox: self.filter_materials(event, cb))
        combobox.bind("<<ComboboxSelected>>", self.on_material_selected)
        self.material_entries[-1]['combobox'].bind("<Return>", self.handle_enter)
        self.material_entries[-1]['quantity_var'].trace_add("write", lambda *args: self.handle_enter(None))

    def remove_material_entry(self, index):
        if len(self.material_entries) > 1:
            entry = self.material_entries.pop(index)
            entry["frame"].destroy()
            for i, entry in enumerate(self.material_entries):
                entry["frame"].winfo_children()[0].configure(text=f"材料 {i+1}:")

    def update_material_list(self, combobox):
        sorted_items = self.data_manager.get_sorted_items_for_recipe()
        materials = [name for name, _ in sorted_items] + list(self.data_manager.get_recipes().keys())
        materials.append("添加新物品")
        combobox['values'] = materials

    def filter_materials(self, event, combobox):
        value = event.widget.get()
        filtered_materials = self.data_manager.filter_materials(value)
        combobox['values'] = filtered_materials
        if value:
            current_values = list(combobox['values'])
            if value not in current_values:
                current_values.append(value + "(添加新物品)")
                combobox['values'] = current_values

    def on_material_selected(self, event):
        selected = event.widget.get()
        if "添加新物品" in selected:
            self.open_add_item_dialog(event.widget)

    def open_add_item_dialog(self, combobox):
        current_value = combobox.get()
        default_name = current_value[:-7]
        add_item_dialog = AddItemDialog(self, self.data_manager, default_name=default_name, callback=lambda name: self.update_material(combobox, name))
        self.wait_window(add_item_dialog)

    def update_material(self, combobox, new_item_name):
        self.update_material_list(combobox)
        if new_item_name:
            combobox.set(new_item_name)

    def load_recipe_data(self):
        recipe = self.data_manager.get_recipes()[self.recipe_name]
        self.product_quantity_var.set(recipe['quantity'])
        for i, material in enumerate(recipe['materials']):
            if i >= len(self.material_entries):
                self.add_material_entry()
            self.material_entries[i]['var'].set(material['name'])
            self.material_entries[i]['quantity_var'].set(material['quantity'])

        self.crafting_level_var.set(recipe.get('crafting_level', 1))
        self.recipe_type_var.set(recipe.get('recipe_type', '其它'))
        self.is_exclusive_var.set(recipe.get('is_exclusive', False))

    def save_recipe(self):
        name = self.name_var.get()
        if not name:
            messagebox.showerror("错误", "请输入配方名称")
            return

        materials = []
        for entry in self.material_entries:
            material = entry['var'].get()
            quantity = entry['quantity_var'].get()
            if material and quantity > 0:
                materials.append({"name": material, "quantity": quantity})

        if not materials:
            messagebox.showerror("错误", "请至少添加一种材料")
            return

        product_quantity = self.product_quantity_var.get()
        crafting_level = self.crafting_level_var.get()
        recipe_type = self.recipe_type_var.get()
        is_exclusive = self.is_exclusive_var.get()

        if product_quantity <= 0 or crafting_level < 1 or crafting_level > 150:
            messagebox.showerror("错误", "产品数量必须大于0，制作等级必须在1到150之间")
            return

        try:
            if self.new_recipe:
                self.data_manager.add_recipe(name, materials, product_quantity, crafting_level, recipe_type, is_exclusive)
                messagebox.showinfo("成功", f"新配方 '{name}' 已添加")
            else:
                self.data_manager.update_recipe(name, materials, product_quantity, crafting_level, recipe_type, is_exclusive)
                if name != self.recipe_name:
                    self.data_manager.delete_recipe(self.recipe_name)
                messagebox.showinfo("成功", f"配方 '{name}' 已更新")
            
            self.result = name
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def delete_recipe(self):
        if messagebox.askyesno("确认删除", f"您确定要删除配方 '{self.recipe_name}' 吗？"):
            try:
                self.data_manager.delete_recipe(self.recipe_name)
                messagebox.showinfo("成功", f"配方 '{self.recipe_name}' 已被删除")
                self.destroy()
            except KeyError as e:
                messagebox.showerror("错误", str(e))

class SelectItemDialog(tk.Toplevel):
    def __init__(self, parent, data_manager, edit_callback):
        super().__init__(parent)
        self.data_manager = data_manager
        self.edit_callback = edit_callback  # 新增：编辑回调函数
        self.title("选择物品")
        self.selected_item = None
        self.all_items = self.data_manager.get_sorted_base_items()
        self.filtered_items = self.all_items.copy()
        self.create_widgets()

    def create_widgets(self):
        # 搜索框
        row = 0
        ttk.Label(self, text="搜索:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self, textvariable=self.search_var)
        self.search_entry.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.search_var.trace("w", self.filter_items)

        # 类别筛选
        row += 1 # row = 1
        ttk.Label(self, text="类别:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.category_var = tk.StringVar(value="所有")
        categories = ["所有"] + list(set(data['category'] for _, data in self.all_items))
        self.category_combobox = ttk.Combobox(self, textvariable=self.category_var, values=categories)
        self.category_combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.category_combobox.bind("<<ComboboxSelected>>", self.filter_items)

        # 品质筛选
        row += 1 # row = 2
        ttk.Label(self, text="品质:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.quality_var = tk.StringVar(value="所有")
        qualities = ["所有"] + list(set(data['quality'] for _, data in self.all_items))
        self.quality_combobox = ttk.Combobox(self, textvariable=self.quality_var, values=qualities)
        self.quality_combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.quality_combobox.bind("<<ComboboxSelected>>", self.filter_items)

        # 等级筛选（新添加）
        row += 1 # row = 3
        ttk.Label(self, text="等级:").grid(row=row, column=0, padx=5, pady=5, sticky="w")
        self.level_var = tk.StringVar(value="所有")
        levels = ["所有"] + sorted(set(data['level'] for _, data in self.all_items))
        self.level_combobox = ttk.Combobox(self, textvariable=self.level_var, values=levels)
        self.level_combobox.grid(row=row, column=1, padx=5, pady=5, sticky="ew")
        self.level_combobox.bind("<<ComboboxSelected>>", self.filter_items)

        # 物品列表
        row += 1 # row = 4
        self.item_listbox = tk.Listbox(self, width=50, height=15)
        self.item_listbox.grid(row=row, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.update_item_list()

        # 滚动条
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.item_listbox.yview)
        scrollbar.grid(row=row, column=2, sticky="ns")
        self.item_listbox.configure(yscrollcommand=scrollbar.set)

        # 确定按钮
        row += 1 # row = 5
        ttk.Button(self, text="确定", command=self.on_ok).grid(row=row, column=0, columnspan=2, pady=10)

        # 设置网格权重
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # 处理双击
        self.item_listbox.bind("<Double-1>", self.on_item_double_click)

    def on_item_double_click(self, event):
        selection = self.item_listbox.curselection()
        if selection:
            index = selection[0]
            selected_item = self.filtered_items[index][0]
            self.edit_callback(selected_item)

    def filter_items(self, *args):
        search_text = self.search_var.get().lower()
        category = self.category_var.get()
        quality = self.quality_var.get()
        level = self.level_var.get()  # 新添加

        self.filtered_items = [
            (name, data) for name, data in self.all_items
            if search_text in name.lower()
            and (category == "所有" or data['category'] == category)
            and (quality == "所有" or str(data['quality']) == quality)
            and (level == "所有" or str(data['level']) == level)  # 新添加
        ]

        self.update_item_list()

    def update_item_list(self):
        self.item_listbox.delete(0, tk.END)
        for name, data in self.filtered_items:
            self.item_listbox.insert(tk.END, f"{name} (等级: {data['level']}, 品质: {data['quality']}, 类别: {data['category']})")

    def on_ok(self):
        selection = self.item_listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_item = self.filtered_items[index][0]
        self.destroy()

class SelectRecipeDialog(tk.Toplevel):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.title("选择配方")
        self.selected_recipe = None
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="选择要编辑的配方:").grid(row=0, column=0, padx=5, pady=5)
        self.recipe_var = tk.StringVar()
        self.recipe_combobox = ttk.Combobox(self, textvariable=self.recipe_var, values=list(self.data_manager.get_recipes().keys()))
        self.recipe_combobox.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self, text="确定", command=self.on_ok).grid(row=1, column=0, columnspan=2, pady=10)

    def on_ok(self):
        self.selected_recipe = self.recipe_var.get()
        self.destroy()

class DataManagementPage(ttk.Frame):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.create_widgets()

    def create_widgets(self):
        # 物品管理部分
        item_frame = ttk.LabelFrame(self, text="物品管理")
        item_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(item_frame, text="添加新物品", command=self.add_new_item).pack(side="left", padx=5)
        ttk.Button(item_frame, text="编辑物品", command=self.edit_item).pack(side="left", padx=5)

        # 配方管理部分
        recipe_frame = ttk.LabelFrame(self, text="配方管理")
        recipe_frame.pack(padx=10, pady=10, fill="x")

        ttk.Button(recipe_frame, text="添加新配方", command=self.add_new_recipe).pack(side="left", padx=5)
        ttk.Button(recipe_frame, text="编辑配方", command=self.edit_recipe).pack(side="left", padx=5)

    def add_new_item(self):
        AddItemDialog(self, self.data_manager)

    def edit_item(self):
        items = self.data_manager.get_sorted_base_items()
        if not items:
            messagebox.showinfo("提示", "当前没有可编辑的物品")
            return

        def edit_callback(item_name):
            AddItemDialog(self, self.data_manager, item_name)

        select_dialog = SelectItemDialog(self, self.data_manager, edit_callback)
        self.wait_window(select_dialog)

        if select_dialog.selected_item:
            edit_callback(select_dialog.selected_item)


    def add_new_recipe(self):
        RecipeDialog(self, self.data_manager)

    def edit_recipe(self):
        recipes = self.data_manager.get_recipes()
        if not recipes:
            messagebox.showinfo("提示", "当前没有可编辑的配方")
            return

        select_dialog = SelectRecipeDialog(self, self.data_manager)
        self.wait_window(select_dialog)
        
        if select_dialog.selected_recipe:
            RecipeDialog(self, self.data_manager, new_recipe=False, recipe_name=select_dialog.selected_recipe)
            
class MaterialTrackingPage(ttk.Frame):
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.selected_items = {}  # Store user-selected items and their quantities
        self.create_widgets()
        self.material_data = None  # 用于存储计算结果 

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # Left frame (70% width)
        self.left_frame = ttk.Frame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        for i in range(5):
            self.left_frame.grid_rowconfigure(i, weight=1)

        # Right frame (30% width)
        self.right_frame = ttk.Frame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

        # Create sections in left frame
        self.create_item_selection(self.left_frame)
        self.create_total_materials(self.left_frame)
        self.create_ticket_materials(self.left_frame)
        self.create_camp_materials(self.left_frame)
        self.create_gold_materials(self.left_frame)
        self.create_unavailable_materials(self.left_frame)

        # Create cost calculation area in right frame
        self.create_cost_calculation(self.right_frame)

    def create_item_selection(self, parent):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Label(frame, text="选择要追踪的成品:").grid(row=0, column=0, sticky="w")

        self.items_frame = ttk.Frame(frame)
        self.items_frame.grid(row=1, column=0, sticky="nsew")
        self.items_frame.grid_columnconfigure(0, weight=1)

        self.item_entries = []
        self.add_item_entry()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=5)
        ttk.Button(button_frame, text="添加物品", command=self.add_item_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="计算材料", command=self.calculate_materials).pack(side=tk.LEFT, padx=5)

    def create_total_materials(self, parent):
        self.total_materials_frame = ttk.LabelFrame(parent, text="总材料清单")
        self.total_materials_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.create_material_display(self.total_materials_frame)

    def create_ticket_materials(self, parent):
        self.ticket_materials_frame = ttk.LabelFrame(parent, text="采集券兑换材料")
        self.ticket_materials_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.create_material_display(self.ticket_materials_frame)
        self.ticket_cost_label = ttk.Label(self.ticket_materials_frame, text="")
        self.ticket_cost_label.grid(row=1, column=0, columnspan=5, sticky="w")

    def create_camp_materials(self, parent):
        self.camp_materials_frame = ttk.LabelFrame(parent, text="营地贡献与新币兑换材料")
        self.camp_materials_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self.create_material_display(self.camp_materials_frame)
        self.camp_cost_label = ttk.Label(self.camp_materials_frame, text="")
        self.camp_cost_label.grid(row=1, column=0, columnspan=5, sticky="w")

    def create_gold_materials(self, parent):
        self.gold_materials_frame = ttk.LabelFrame(parent, text="金条购买材料")
        self.gold_materials_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        self.create_material_display(self.gold_materials_frame)
        self.gold_cost_label = ttk.Label(self.gold_materials_frame, text="")
        self.gold_cost_label.grid(row=1, column=0, columnspan=5, sticky="w")

    def create_unavailable_materials(self, parent):
        self.unavailable_materials_frame = ttk.LabelFrame(parent, text="无法购买的材料")
        self.unavailable_materials_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        self.create_material_display(self.unavailable_materials_frame)
        self.shortage_label = ttk.Label(self.unavailable_materials_frame, text="", foreground="red")
        self.shortage_label.grid(row=1, column=0, columnspan=5, sticky="w")

    def create_material_display(self, parent):
        categories = ["木材", "矿物", "麻料", "怪物", "其它"]
        for i, category in enumerate(categories):
            frame = ttk.Frame(parent)
            frame.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            parent.grid_columnconfigure(i, weight=1)
            ttk.Label(frame, text=category).pack()
            listbox = tk.Listbox(frame, height=5)
            listbox.pack(fill=tk.BOTH, expand=True)
            setattr(self, f"{parent.winfo_name()}_listbox_{category}", listbox)

    def create_cost_calculation(self, parent):
        cost_frame = ttk.Frame(parent)
        cost_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        cost_frame.grid_columnconfigure(0, weight=1)
        cost_frame.grid_rowconfigure(0, weight=1)

        # Create 3D plot
        self.fig = Figure(figsize=(4, 3), dpi=100)  # Adjusted figure size
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=cost_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Create input controls
        control_frame = ttk.Frame(cost_frame)
        control_frame.grid(row=1, column=0, sticky="ew", pady=10)
        control_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="最大可用采集券:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.max_tickets = tk.IntVar(value=-1)
        ttk.Entry(control_frame, textvariable=self.max_tickets, width=10).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Scale(control_frame, from_=-1, to=200000, variable=self.max_tickets, command=self.update_plot).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ttk.Label(control_frame, text="最大可用营地贡献:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.max_camp = tk.IntVar(value=-1)
        ttk.Entry(control_frame, textvariable=self.max_camp, width=10).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Scale(control_frame, from_=-1, to=150000, variable=self.max_camp, command=self.update_plot).grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        ttk.Label(control_frame, text="最大可用新币:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.max_new_dollar = tk.IntVar(value=-1)
        ttk.Entry(control_frame, textvariable=self.max_new_dollar, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Scale(control_frame, from_=-1, to=400000, variable=self.max_new_dollar, command=self.update_plot).grid(row=2, column=2, padx=5, pady=5, sticky="ew")

    def add_item_entry(self):

        index = len(self.item_entries)
        frame = ttk.Frame(self.items_frame)
        frame.grid(row=index, column=0, sticky="ew", padx=5, pady=2)

        var = tk.StringVar()
        combobox = ttk.Combobox(frame, textvariable=var)
        combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        quantity_var = tk.IntVar(value=1)
        quantity_entry = ttk.Entry(frame, textvariable=quantity_var, width=5)
        quantity_entry.pack(side=tk.LEFT, padx=5)
        
        remove_button = ttk.Button(frame, text="X", width=2, command=lambda: self.remove_item_entry(frame))
        remove_button.pack(side=tk.LEFT, padx=5)

        self.item_entries.append({
            "frame": frame,
            "var": var,
            "combobox": combobox,
            "quantity_var": quantity_var
        })

        self.update_item_list(combobox)
        combobox.bind("<KeyRelease>", lambda event: self.filter_recipes(event, combobox))
        combobox.bind("<<ComboboxSelected>>", lambda event: self.on_recipe_selected(event, combobox))

    def remove_item_entry(self, frame):
        if len(self.item_entries) > 1:
            frame.destroy()
            self.item_entries = [entry for entry in self.item_entries if entry["frame"] != frame]
            for i, entry in enumerate(self.item_entries):
                entry["frame"].grid(row=i, column=0)

    def calculate_materials(self):
        self.selected_items = {}
        for entry in self.item_entries:
            item = entry["var"].get()
            quantity = entry["quantity_var"].get()
            if item and quantity > 0:
                self.selected_items[item] = quantity

        self.total_materials = self.get_total_materials()
        self.base_materials_data = self.data_manager.get_base_materials_data()
        self.calculate_costs()
        self.update_displays()

    def get_total_materials(self):
        total_materials = {}
        for item, quantity in self.selected_items.items():
            materials = self.get_base_materials(item, quantity)
            for material, amount in materials.items():
                if material in total_materials:
                    total_materials[material] += amount
                else:
                    total_materials[material] = amount
        return total_materials

    def get_base_materials(self, item, quantity):
        base_materials = {}
        if item in self.data_manager.get_recipes():
            recipe = self.data_manager.get_recipes()[item]
            for material in recipe["materials"]:
                material_name = material["name"]
                material_quantity = material["quantity"] * quantity / recipe["quantity"]
                sub_materials = self.get_base_materials(material_name, material_quantity)
                for sub_material, sub_quantity in sub_materials.items():
                    if sub_material in base_materials:
                        base_materials[sub_material] += sub_quantity
                    else:
                        base_materials[sub_material] = sub_quantity
        else:
            base_materials[item] = quantity
        return base_materials

    def calculate_costs(self):
        materials_data = self.prepare_materials_data()
        self.A, self.B, self.C = self.split_materials(materials_data)
        self.A_expand = self.expand_A(self.A)
        self.B_expand = self.expand_B(self.B)

        # 只在 A_expand 或 B_expand 发生变化时才重新计算 plot_data
        if not hasattr(self, 'plot_data') or (hasattr(self, 'prev_A_expand') and self.prev_A_expand != self.A_expand) or (hasattr(self, 'prev_B_expand') and self.prev_B_expand != self.B_expand):
            self.plot_data = self.create_plot_data()
            self.prev_A_expand = self.A_expand.copy()
            self.prev_B_expand = self.B_expand.copy()

        # 计算材料数据并存储
        self.material_data = self.calculate_material_data()

    def calculate_material_data(self):
        A1, A2, A3, temp_A = self.calculate_A_materials()
        B1, B2, B3, temp_B = self.calculate_B_materials()
        C2, C3, temp_C = self.calculate_C_materials()
        return {
            'A1': A1, 'A2': A2, 'A3': A3, 'temp_A': temp_A,
            'B1': B1, 'B2': B2, 'B3': B3, 'temp_B': temp_B,
            'C2': C2, 'C3': C3, 'temp_C': temp_C
        }
    
    def update_displays(self):
        self.update_plot()
        self.update_material_displays()

    def prepare_materials_data(self):
        materials_data = []
        for material, quantity in self.total_materials.items():
            item_data = self.base_materials_data[material]
            channel_label = 1 if item_data['ticket_price'] != -1 else (2 if item_data['camp_contribution'] != -1 else 3)
            channel_price = item_data['ticket_price'] if channel_label == 1 else \
                            (item_data['camp_contribution'], item_data['new_dollar']) if channel_label == 2 else \
                            item_data['price']
            purchase_price = item_data['price']
            materials_data.append([material, quantity, channel_label, channel_price, purchase_price])
        return materials_data

    def split_materials(self, materials_data):
        A = [m for m in materials_data if m[2] == 1]
        B = [m for m in materials_data if m[2] == 2]
        C = [m for m in materials_data if m[2] == 3]
        A.sort(key=lambda x: x[3]/x[4])
        B.sort(key=lambda x: x[3][0]/x[4])
        return A, B, C

    def expand_A(self, A):
        ticket_cost = 0
        gold_cost_A = sum(m[1] * m[4] for m in A if m[4] != -1)
        A_expand = []
        for material, quantity, _, ticket_price, gold_price in A:
            for _ in range(self.data_manager.round_quantity(quantity)):
                ticket_cost += ticket_price
                if gold_price != -1:
                    gold_cost_A -= gold_price
                A_expand.append([material, ticket_cost, gold_cost_A])
        return A_expand

    def expand_B(self, B):
        camp_cost = 0
        new_dollar_cost = 0
        gold_cost_B = sum(m[1] * m[4] for m in B if m[4] != -1)
        B_expand = []
        for material, quantity, _, (camp_price, new_dollar_price), gold_price in B:
            for _ in range(self.data_manager.round_quantity(quantity)):
                camp_cost += camp_price
                new_dollar_cost += new_dollar_price
                if gold_price != -1:
                    gold_cost_B -= gold_price
                B_expand.append([material, camp_cost, new_dollar_cost, gold_cost_B])
        return B_expand

    def create_plot_data(self):
        if not self.A_expand or not self.B_expand:
            return np.array([]), np.array([]), np.array([])

        # 直接使用 A_expand 和 B_expand 中的票券和营地贡献值
        ticket_values = [a[1] for a in self.A_expand]
        camp_values = [b[1] for b in self.B_expand]

        X, Y = np.meshgrid(ticket_values, camp_values)
        Z = np.zeros_like(X)

        # 使用向量化操作来填充 Z
        A_gold = np.array([a[2] for a in self.A_expand])
        B_gold = np.array([b[3] for b in self.B_expand])

        Z = A_gold[np.newaxis, :] + B_gold[:, np.newaxis]

        return X, Y, Z

    def update_material_displays(self):
        if not self.material_data:
            return
        
        self.update_total_materials()
        self.update_ticket_materials()
        self.update_camp_materials()
        self.update_gold_materials()
        self.update_unavailable_materials()

    def update_total_materials(self):
        self.display_materials(self.total_materials_frame, self.total_materials)

    def update_ticket_materials(self):
        infi = '\u221E'
        A1 = self.material_data['A1']
        temp_A = self.material_data['temp_A']
        self.display_materials(self.ticket_materials_frame, A1)
        self.ticket_cost_label.config(text=f"兑换花费: {temp_A[1]} 采集券, 余额: {self.max_tickets.get() - temp_A[1] if self.max_tickets.get() != -1 else infi}")

    def update_camp_materials(self):
        infi = '\u221E'
        B1 = self.material_data['B1']
        temp_B = self.material_data['temp_B']
        self.display_materials(self.camp_materials_frame, B1)
        self.camp_cost_label.config(text=f"兑换花费: {temp_B[1]} 营地贡献, {temp_B[2]} 新币, "
                                         f"余额: {self.max_camp.get() - temp_B[1] if self.max_camp.get() != -1 else infi} 营地贡献, {self.max_new_dollar.get() - temp_B[2] if self.max_new_dollar.get() != -1 else infi} 新币")

    def update_gold_materials(self):
        A2 = self.material_data['A2']
        B2 = self.material_data['B2']
        C2 = self.material_data['C2']
        temp_A = self.material_data['temp_A']
        temp_B = self.material_data['temp_B']
        temp_C = self.material_data['temp_C']
        gold_materials = {**A2, **B2, **C2}
        self.display_materials(self.gold_materials_frame, gold_materials)
        self.gold_cost_label.config(text=f"购买花费: {temp_A[2] + temp_B[3] + temp_C} 金条")

    def update_unavailable_materials(self):
        infi = '\u221E'
        A3 = self.material_data['A3']
        B3 = self.material_data['B3']
        C3 = self.material_data['C3']
        temp_A = self.material_data['temp_A']
        temp_B = self.material_data['temp_B']
        unavailable_materials = {**A3, **B3, **C3}
        self.display_materials(self.unavailable_materials_frame, unavailable_materials)

        ticket_shortage = ((self.A_expand[-1][1] - self.max_tickets.get()) if temp_A != self.A_expand[-1] else 0) if self.A_expand else 0
        camp_shortage = ((self.B_expand[-1][1] - self.max_camp.get()) if temp_B != self.B_expand[-1] else 0) if self.B_expand else 0
        new_dollar_shortage = ((self.B_expand[-1][2] - self.max_new_dollar.get()) if temp_B != self.B_expand[-1] else 0) if self.B_expand else 0
        
        shortage_text = f"缺口: {ticket_shortage} 采集券, {camp_shortage} 营地贡献, {new_dollar_shortage} 新币"
        self.shortage_label.config(text=shortage_text)

    def display_materials(self, parent, materials):
        categories = ["木材", "矿物", "麻料", "怪物", "其它"]
        for category in categories:
            listbox = getattr(self, f"{parent.winfo_name()}_listbox_{category}")
            listbox.delete(0, tk.END)
            for material, quantity in materials.items():
                quantity = self.data_manager.round_quantity(quantity)
                if self.base_materials_data[material]['category'] == category and quantity > 0:
                    listbox.insert(tk.END, f"{material}: {quantity}")

    def calculate_A_materials(self):
        A1 = {item[0]: 0 for item in self.A}
        A2 = A1.copy()
        A3 = A1.copy()
        
        max_tickets = self.max_tickets.get()
        if max_tickets == -1:
            for item in self.A:
                A1[item[0]] = item[1]
            temp_A = self.A_expand[-1] if self.A_expand else [None, 0, 0]
        else:
            temp_A = [None, 0, 0]
            for item in self.A_expand:
                if max_tickets >= item[1]:
                    A1[item[0]] += 1
                    temp_A = item
                else:
                    if item[2] != -1:
                        A2[item[0]] += 1
                    else:
                        A3[item[0]] += 1
        
        return A1, A2, A3, temp_A

    def calculate_B_materials(self):
        B1 = {item[0]: 0 for item in self.B}
        B2 = B1.copy()
        B3 = B1.copy()
        
        max_camp = self.max_camp.get()
        max_new_dollar = self.max_new_dollar.get()
        
        if max_camp == -1 and max_new_dollar == -1:
            for item in self.B:
                B1[item[0]] = item[1]
            temp_B = self.B_expand[-1] if self.B_expand else [None, 0, 0, 0]
        else:
            temp_B = [None, 0, 0, 0]
            for item in self.B_expand:
                if (max_camp == -1 or max_camp >= item[1]) and (max_new_dollar == -1 or max_new_dollar >= item[2]):
                    B1[item[0]] += 1
                    temp_B = item
                else:
                    if item[3] != -1:
                        B2[item[0]] += 1
                    else:
                        B3[item[0]] += 1
        
        return B1, B2, B3, temp_B
    
    def calculate_C_materials(self):
        C2 = {item[0]:0 for item in self.C}
        C3 = C2.copy()
        temp_C = 0
        for item in self.C:
            if item[3] != -1:# 使用索引4来检查金条价格
                C2[item[0]] = item[1]
                temp_C += item[1] * item[3]# 使用索引4来获取金条价格
            else:
                C3[item[0]] = item[1]
        return C2, C3, temp_C


    def update_plot(self, *args):
        if not hasattr(self, 'plot_data') or not self.material_data:
            return

        X, Y, Z = self.plot_data
        temp_A = self.material_data['temp_A']
        temp_B = self.material_data['temp_B']

        self.ax.clear()
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # 确保 Z 是二维的
        if Z.ndim == 1:
            print(Z)
        else:
            surf = self.ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)
            self.fig.colorbar(surf, ax=self.ax, label='金条')

            self.ax.set_xlabel('采集券')
            self.ax.set_ylabel('营地贡献')
            self.ax.set_zlabel('金条')

            if temp_A[1] is not None:
                x_highlight = temp_A[1]
                x_index = np.searchsorted(X[0], x_highlight)
                if x_index < X.shape[1]:
                    self.ax.plot([x_highlight, x_highlight], [Y[:,x_index].min(), Y[:,x_index].max()], 
                                [Z[:,x_index].max(), Z[:,x_index].min()], color='r', linewidth=2)

            if temp_B[1] is not None:
                y_highlight = temp_B[1]
                y_index = np.searchsorted(Y[:,0], y_highlight)
                if y_index < Y.shape[0]:
                    self.ax.plot([X[y_index].min(), X[y_index].max()], [y_highlight, y_highlight], 
                                [Z[y_index].max(), Z[y_index].min()], color='r', linewidth=2)

            if temp_A[1] is not None and temp_B[1] is not None:
                x_index = np.searchsorted(X[0], temp_A[1])
                y_index = np.searchsorted(Y[:,0], temp_B[1])
                if x_index < X.shape[1] and y_index < Y.shape[0]:
                    z_value = Z[y_index, x_index]
                    self.ax.scatter([temp_A[1]], [temp_B[1]], [z_value], color='r', s=100, marker='*')

            self.ax.view_init(elev=20, azim=45)
            self.canvas.draw()

    def update_item_list(self, combobox):
        recipes = list(self.data_manager.get_recipes().keys())
        combobox['values'] = recipes

    def filter_recipes(self, event, combobox):
        value = event.widget.get()
        recipes = self.data_manager.get_recipes().keys()
        filtered_recipes = [recipe for recipe in recipes if value.lower() in recipe.lower()]
        
        if value and value not in filtered_recipes:
            filtered_recipes.append(f"{value}(添加新配方)")
        
        combobox['values'] = filtered_recipes

    def on_recipe_selected(self, event, combobox):
        selected = combobox.get()
        if "添加新配方" in selected:
            self.open_add_recipe_dialog(combobox)

    def open_add_recipe_dialog(self, combobox):
        current_value = combobox.get()
        default_name = current_value[:-7] if "(添加新配方)" in current_value else current_value
        recipe_dialog = RecipeDialog(self, self.data_manager, new_recipe=True, recipe_name=default_name)
        self.wait_window(recipe_dialog)
        if recipe_dialog.result:
            self.update_item_list(combobox)
            combobox.set(recipe_dialog.result)  # 使用新配方的名称更新 Combobox

class CraftingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("绿鬣蜥")
        self.geometry("1280x720")  # 可能需要调整大小

        self.data_manager = DataManager()

        self.create_menu()
        self.create_notebook()

    def create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开数据文件", command=self.open_data_file)
        file_menu.add_command(label="退出", command=self.quit)
            
    def open_data_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.data_manager.load_data(file_path)
            self.update_ui()
            messagebox.showinfo("成功", f"已加载数据文件: {file_path}")

    def create_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self.crafting_page = CraftingPage(self.notebook, self.data_manager)
        self.data_management_page = DataManagementPage(self.notebook, self.data_manager)
        self.material_tracking_page = MaterialTrackingPage(self.notebook, self.data_manager)

        self.notebook.add(self.crafting_page, text="制作查询")
        self.notebook.add(self.material_tracking_page, text="材料追踪")
        self.notebook.add(self.data_management_page, text="数据管理")

    def update_ui(self):
        # 更新制作页面
        self.crafting_page.update_item_list()
        self.crafting_page.update_info()
        
        # 更新数据管理页面（如果需要的话）
        self.material_tracking_page.update_item_list(self.material_tracking_page.item_entries[0]['combobox'])

if __name__ == "__main__":
    app = CraftingApp()
    app.mainloop()