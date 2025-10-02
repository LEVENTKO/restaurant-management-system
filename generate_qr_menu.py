#!/usr/bin/env python3
"""
QR Menu Carbon Calculator - Working Version
==========================================
A complete QR menu system with carbon footprint calculation for restaurants.
"""

import os
import json
import qrcode
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class MenuItem:
    name: str
    price: float
    description: str
    carbon_footprint: float
    is_eco_friendly: bool
    ingredients: List[str]
    cooking_methods: List[str]

class CarbonCalculator:
    """Simple carbon footprint calculator"""
    
    def __init__(self):
        # Carbon factors (kg CO2 per kg ingredient)
        self.carbon_factors = {
            'beef': 27.0, 'lamb': 39.2, 'pork': 12.1, 
            'chicken': 6.9, 'fish': 6.1, 'salmon': 6.1,
            'cheese': 13.5, 'milk': 3.2, 'butter': 23.8, 'eggs': 4.8,
            'rice': 2.7, 'pasta': 0.9, 'bread': 0.9,
            'vegetables': 2.0, 'tomatoes': 2.1, 'potatoes': 0.5,
            'fruits': 1.1, 'olive_oil': 6.0, 'nuts': 2.3,
            'beans': 2.0, 'quinoa': 1.5
        }
        
        # Cooking method carbon factors (kg CO2 per hour)
        self.cooking_factors = {
            'oven': 2.1, 'stovetop': 1.8, 'grill': 3.5,
            'deep_fry': 4.2, 'microwave': 0.6, 'steam': 1.0,
            'raw': 0.0
        }
    
    def estimate_carbon_footprint(self, dish_name: str) -> Dict:
        """Estimate carbon footprint based on dish name"""
        dish_lower = dish_name.lower()
        
        # Simple ingredient estimation
        ingredients = []
        total_carbon = 0.0
        
        # Protein detection
        if any(meat in dish_lower for meat in ['beef', 'steak', 'hamburger']):
            ingredients.append('beef')
            total_carbon += 27.0 * 0.25  # 250g beef
        elif any(chicken in dish_lower for chicken in ['chicken', 'tavuk']):
            ingredients.append('chicken')
            total_carbon += 6.9 * 0.2  # 200g chicken
        elif any(fish in dish_lower for fish in ['fish', 'salmon', 'balık']):
            ingredients.append('fish')
            total_carbon += 6.1 * 0.18  # 180g fish
        elif any(pork in dish_lower for pork in ['pork', 'bacon', 'ham']):
            ingredients.append('pork')
            total_carbon += 12.1 * 0.2  # 200g pork
        elif any(lamb in dish_lower for lamb in ['lamb', 'kuzu']):
            ingredients.append('lamb')
            total_carbon += 39.2 * 0.2  # 200g lamb
        
        # Carbs detection
        if any(pasta in dish_lower for pasta in ['pasta', 'spaghetti', 'makarna']):
            ingredients.append('pasta')
            total_carbon += 0.9 * 0.1  # 100g pasta
        elif any(rice in dish_lower for rice in ['rice', 'pilav', 'risotto']):
            ingredients.append('rice')
            total_carbon += 2.7 * 0.1  # 100g rice
        elif any(bread in dish_lower for bread in ['sandwich', 'burger', 'bread']):
            ingredients.append('bread')
            total_carbon += 0.9 * 0.08  # 80g bread
        elif any(quinoa in dish_lower for quinoa in ['quinoa']):
            ingredients.append('quinoa')
            total_carbon += 1.5 * 0.1  # 100g quinoa
        
        # Vegetables (always add some)
        if any(salad in dish_lower for salad in ['salad', 'salata', 'vegetables']):
            ingredients.append('vegetables')
            total_carbon += 2.0 * 0.2  # 200g vegetables
        else:
            ingredients.append('vegetables')
            total_carbon += 2.0 * 0.1  # 100g vegetables
        
        # Dairy
        if any(cheese in dish_lower for cheese in ['cheese', 'peynir', 'parmesan']):
            ingredients.append('cheese')
            total_carbon += 13.5 * 0.05  # 50g cheese
        
        # Cooking method detection
        cooking_methods = []
        cooking_carbon = 0.0
        cooking_time = 20  # default minutes
        
        if any(grilled in dish_lower for grilled in ['grilled', 'ızgara', 'grill']):
            cooking_methods.append('grill')
            cooking_carbon = 3.5 * (cooking_time / 60)
        elif any(fried in dish_lower for fried in ['fried', 'kızartma']):
            cooking_methods.append('deep_fry')
            cooking_carbon = 4.2 * (15 / 60)  # 15 min frying
        elif any(baked in dish_lower for baked in ['baked', 'roasted', 'fırın']):
            cooking_methods.append('oven')
            cooking_carbon = 2.1 * (30 / 60)  # 30 min baking
        elif any(raw in dish_lower for raw in ['salad', 'fresh', 'raw']):
            cooking_methods.append('raw')
            cooking_carbon = 0.0
        else:
            cooking_methods.append('stovetop')
            cooking_carbon = 1.8 * (cooking_time / 60)
        
        total_carbon += cooking_carbon
        
        return {
            'ingredients': ingredients,
            'cooking_methods': cooking_methods,
            'total_carbon': round(total_carbon, 2),
            'is_eco_friendly': total_carbon < 2.0
        }

class QRMenuSystem:
    """Main QR Menu System"""
    
    def __init__(self, restaurant_name: str = "Green Restaurant"):
        self.restaurant_name = restaurant_name
        self.calculator = CarbonCalculator()
        self.menu_items = []
    
    def add_menu_item(self, name: str, price: float, description: str = "") -> MenuItem:
        """Add a menu item with carbon calculation"""
        print(f"Adding: {name}")
        
        # Calculate carbon footprint
        carbon_data = self.calculator.estimate_carbon_footprint(name)
        
        # Create menu item
        item = MenuItem(
            name=name,
            price=price,
            description=description or f"Delicious {name.lower()}",
            carbon_footprint=carbon_data['total_carbon'],
            is_eco_friendly=carbon_data['is_eco_friendly'],
            ingredients=carbon_data['ingredients'],
            cooking_methods=carbon_data['cooking_methods']
        )
        
        self.menu_items.append(item)
        
        eco_status = "🌱 Eco-friendly" if item.is_eco_friendly else "🔥 High carbon"
        print(f"  → {item.carbon_footprint} kg CO2 - {eco_status}")
        
        return item
    
    def generate_qr_code(self, filename: str = "qr_menu.png") -> str:
        """Generate QR code"""
        try:
            menu_url = f"https://your-restaurant.com/menu/1"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(menu_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filename)
            
            print(f"✅ QR code saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ QR code generation failed: {e}")
            return ""
    
    def generate_html_menu(self, filename: str = "digital_menu.html") -> str:
        """Generate HTML menu"""
        try:
            # Calculate statistics
            total_items = len(self.menu_items)
            eco_items = sum(1 for item in self.menu_items if item.is_eco_friendly)
            avg_carbon = sum(item.carbon_footprint for item in self.menu_items) / total_items if total_items > 0 else 0
            
            # Sort items by carbon footprint
            sorted_items = sorted(self.menu_items, key=lambda x: x.carbon_footprint)
            
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.restaurant_name} - Digital Menu</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .stats {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
        .menu-item {{ padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .menu-item.eco {{ border-left: 4px solid #28a745; background: #f8fff9; }}
        .item-info {{ flex: 1; }}
        .item-name {{ font-weight: bold; font-size: 18px; margin-bottom: 5px; }}
        .item-description {{ color: #666; margin-bottom: 5px; }}
        .carbon-info {{ font-size: 14px; color: #28a745; }}
        .carbon-high {{ color: #dc3545; }}
        .item-price {{ font-weight: bold; font-size: 18px; color: #e74c3c; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; background: #e8f5e8; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.restaurant_name}</h1>
            <p>🌱 Sustainable Digital Menu with Carbon Footprint</p>
        </div>
        
        <div class="stats">
            <strong>Menu Statistics:</strong> 
            {total_items} items • {eco_items} eco-friendly ({eco_items/total_items*100:.0f}%) • 
            Average: {avg_carbon:.1f} kg CO2
        </div>
        
        <div class="menu-items">"""
            
            for item in sorted_items:
                eco_class = "eco" if item.is_eco_friendly else ""
                carbon_class = "carbon-high" if item.carbon_footprint > 4.0 else ""
                eco_icon = "🌱" if item.is_eco_friendly else ""
                
                html += f"""
            <div class="menu-item {eco_class}">
                <div class="item-info">
                    <div class="item-name">{item.name} {eco_icon}</div>
                    <div class="item-description">{item.description}</div>
                    <div class="carbon-info {carbon_class}">
                        🌍 {item.carbon_footprint} kg CO2 • 
                        Ingredients: {', '.join(item.ingredients[:3])}
                    </div>
                </div>
                <div class="item-price">{item.price:.2f} ₺</div>
            </div>"""
            
            html += f"""
        </div>
        
        <div class="footer">
            <h3>🌱 Thank you for choosing sustainable dining!</h3>
            <p>Look for the 🌱 symbol for our most eco-friendly choices (under 2.0 kg CO2)</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
</body>
</html>"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"✅ HTML menu saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ HTML generation failed: {e}")
            return ""
    
    def generate_report(self, filename: str = "sustainability_report.txt") -> str:
        """Generate sustainability report"""
        try:
            total_items = len(self.menu_items)
            if total_items == 0:
                return ""
            
            eco_items = sum(1 for item in self.menu_items if item.is_eco_friendly)
            avg_carbon = sum(item.carbon_footprint for item in self.menu_items) / total_items
            
            # Get top and bottom items
            sorted_items = sorted(self.menu_items, key=lambda x: x.carbon_footprint)
            lowest_carbon = sorted_items[:3]
            highest_carbon = sorted_items[-3:]
            
            report = f"""SUSTAINABILITY REPORT - {self.restaurant_name}
{'='*60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
- Total Menu Items: {total_items}
- Eco-Friendly Items: {eco_items} ({eco_items/total_items*100:.1f}%)
- Average Carbon Footprint: {avg_carbon:.2f} kg CO2

CARBON DISTRIBUTION:
- Low Carbon (< 2.0 kg): {len([i for i in self.menu_items if i.carbon_footprint < 2.0])} items
- Medium Carbon (2.0-4.0 kg): {len([i for i in self.menu_items if 2.0 <= i.carbon_footprint < 4.0])} items  
- High Carbon (> 4.0 kg): {len([i for i in self.menu_items if i.carbon_footprint >= 4.0])} items

MOST ECO-FRIENDLY ITEMS:
{chr(10).join(f'• {item.name}: {item.carbon_footprint} kg CO2' for item in lowest_carbon)}

HIGHEST CARBON ITEMS:
{chr(10).join(f'• {item.name}: {item.carbon_footprint} kg CO2' for item in highest_carbon)}

RECOMMENDATIONS:
- Target: 50%+ eco-friendly items (currently {eco_items/total_items*100:.1f}%)
- Consider plant-based alternatives for high-carbon items
- Promote seasonal, local ingredients
- Use efficient cooking methods
- Highlight eco-friendly options to customers

NEXT STEPS:
1. Train staff on sustainability messaging
2. Print QR codes for table placement  
3. Monitor customer engagement
4. Update menu seasonally
5. Track progress monthly
"""
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"✅ Report saved: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return ""
    
    def create_sample_menu(self):
        """Create sample menu items"""
        sample_items = [
            ("Mediterranean Quinoa Bowl", 35.00, "Fresh quinoa with vegetables and herbs"),
            ("Grilled Chicken Caesar Salad", 45.00, "Grilled chicken with romaine and parmesan"),
            ("Classic Beef Burger", 55.00, "Beef patty with lettuce, tomato, cheese"),
            ("Fresh Salmon with Herbs", 75.00, "Grilled salmon with seasonal herbs"),
            ("Vegetarian Pasta Primavera", 40.00, "Pasta with fresh seasonal vegetables"),
            ("Turkish Lamb Kebab", 65.00, "Traditional lamb kebab with rice"),
            ("Organic Garden Salad", 25.00, "Fresh organic greens with olive oil"),
            ("Mushroom Risotto", 50.00, "Creamy risotto with wild mushrooms"),
            ("Fish and Chips", 48.00, "Beer battered fish with potato chips"),
            ("Seasonal Fruit Bowl", 20.00, "Fresh seasonal fruits")
        ]
        
        for name, price, description in sample_items:
            self.add_menu_item(name, price, description)

def main():
    """Main function"""
    print("🌱 QR Menu Carbon Calculator")
    print("=" * 40)
    
    # Get restaurant name
    restaurant_name = input("Enter restaurant name (or press Enter for 'Green Bistro'): ").strip()
    if not restaurant_name:
        restaurant_name = "Green Bistro"
    
    # Create system
    system = QRMenuSystem(restaurant_name)
    
    # Menu choice
    print("\nChoose an option:")
    print("1. Create sample menu (recommended)")
    print("2. Add custom items")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        print("\nAdd menu items (empty name to finish):")
        while True:
            name = input("Item name: ").strip()
            if not name:
                break
            try:
                price = float(input(f"Price for '{name}': "))
                description = input(f"Description (optional): ").strip()
                system.add_menu_item(name, price, description)
            except ValueError:
                print("Invalid price, please enter a number")
    else:
        print(f"\nCreating sample menu for {restaurant_name}...")
        system.create_sample_menu()
    
    # Generate outputs
    print(f"\nGenerating files...")
    html_file = system.generate_html_menu()
    qr_file = system.generate_qr_code()
    report_file = system.generate_report()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 QR Menu System Created Successfully!")
    print("=" * 50)
    print(f"Restaurant: {restaurant_name}")
    print(f"Menu Items: {len(system.menu_items)}")
    print(f"Eco-friendly: {sum(1 for i in system.menu_items if i.is_eco_friendly)}")
    
    if html_file:
        print(f"📱 Digital Menu: {html_file}")
    if qr_file:
        print(f"📄 QR Code: {qr_file}")
    if report_file:
        print(f"📊 Report: {report_file}")
    
    print("\n🚀 Next Steps:")
    print("1. Open the HTML file in your browser")
    print("2. Print the QR code for tables")
    print("3. Review the sustainability report")
    
    print("\n🌱 Happy sustainable dining!")

if __name__ == "__main__":
    main()
