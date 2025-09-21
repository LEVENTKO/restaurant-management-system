#!/usr/bin/env python3
"""
Complete Restaurant Management System - FIXED VERSION
QR Menu Software + Carbon Footprint Calculator + OCR Menu Reader
All bugs fixed including OCR item addition
"""

import streamlit as st
import pandas as pd
import json
import hashlib
import qrcode
from io import BytesIO
import base64
import uuid
from typing import Dict, List, Tuple
import re

# Optional imports for OCR functionality
try:
    from PIL import Image
    import pytesseract
    import cv2
    import numpy as np

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Page config - must be first
st.set_page_config(
    page_title="Restaurant Management System",
    page_icon="🍽️",
    layout="wide"
)


class AdminConfig:
    def __init__(self):
        self.default_admin = {
            'username': 'admin',
            'password': self.hash_password('committed123')
        }

        if 'admin_config' not in st.session_state:
            st.session_state.admin_config = self.load_default_config()
        if 'restaurants' not in st.session_state:
            st.session_state.restaurants = {}
        if 'menus' not in st.session_state:
            st.session_state.menus = {}

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed: str) -> bool:
        return self.hash_password(password) == hashed

    def load_default_config(self) -> Dict:
        return {
            'thresholds': {
                'low_impact': 2.0,
                'medium_impact': 5.0
            },
            'emission_factors': {
                'beef': 60.0, 'lamb': 24.0, 'pork': 7.2, 'chicken': 6.1,
                'fish': 4.0, 'salmon': 5.1, 'eggs': 4.2, 'cheese': 21.0,
                'milk': 3.2, 'rice': 2.7, 'pasta': 1.4, 'potatoes': 0.3,
                'tomatoes': 1.4, 'lettuce': 0.2, 'mushrooms': 0.7,
                'oil': 3.2, 'butter': 9.0, 'bread': 1.3, 'onion': 0.3,
                'garlic': 0.5, 'pepper': 2.0, 'cucumber': 0.2, 'carrot': 0.3
            },
            'fixed_emissions': {
                'cooking': 0.3,
                'packaging': 0.05,
                'customer_travel': 0.5
            }
        }


class MenuOCRProcessor:
    def __init__(self):
        self.common_food_words = [
            'pizza', 'burger', 'pasta', 'salad', 'chicken', 'beef', 'fish', 'soup',
            'sandwich', 'wrap', 'steak', 'rice', 'noodles', 'bread', 'cheese',
            'tomato', 'onion', 'garlic', 'pepper', 'sauce', 'cream', 'butter',
            'oil', 'wine', 'beer', 'coffee', 'tea', 'juice', 'water', 'meat',
            'vegetable', 'fruit', 'potato', 'lettuce', 'mushroom', 'egg'
        ]

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert PIL image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)

            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)

            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            return thresh
        except Exception as e:
            st.error(f"Image preprocessing error: {str(e)}")
            return np.array(image.convert('L'))

    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from menu image using OCR"""
        if not OCR_AVAILABLE:
            return ""

        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)

            # Configure tesseract for better results
            custom_config = r'--oem 3 --psm 6'

            # Extract text
            text = pytesseract.image_to_string(processed_image, config=custom_config)

            return text
        except Exception as e:
            st.error(f"OCR Error: {str(e)}. Make sure Tesseract is installed.")
            return ""

    def parse_menu_items(self, text: str) -> List[Dict]:
        """Parse extracted text to identify menu items and prices"""
        items = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue

            # Look for price patterns
            price_pattern = r'[\₺\$\€\£]?\s*\d+[\.,]?\d*\s*[\₺\$\€\£]?'
            price_matches = re.findall(price_pattern, line)

            # Extract potential item name
            item_text = re.sub(price_pattern, '', line).strip()

            # Filter out very short or non-food related text
            if len(item_text) > 3:
                # Check if it contains food-related words
                food_score = sum(1 for word in self.common_food_words
                                 if word.lower() in item_text.lower())

                if food_score > 0:
                    # Extract price if found
                    price = 0.0
                    if price_matches:
                        price_str = re.sub(r'[^\d\.,]', '', price_matches[-1])
                        try:
                            price = float(price_str.replace(',', '.'))
                        except:
                            price = 0.0

                    # Guess ingredients based on common food words
                    ingredients = []
                    for word in self.common_food_words:
                        if word.lower() in item_text.lower():
                            ingredients.append(word)

                    confidence = (food_score * 0.2) + (0.5 if price > 0 else 0)

                    items.append({
                        'name': item_text,
                        'price': price,
                        'ingredients': ', '.join(ingredients[:4]),
                        'description': '',
                        'vegetarian': any(veg in item_text.lower()
                                          for veg in ['vegetarian', 'vegan', 'salad', 'veggie']),
                        'available': True,
                        'confidence': min(confidence, 1.0)
                    })

        # Sort by confidence and return top items
        items.sort(key=lambda x: x['confidence'], reverse=True)
        return items[:15]


class RestaurantManager:
    def __init__(self):
        self.restaurants = st.session_state.restaurants
        self.menus = st.session_state.menus

    def create_restaurant(self, name: str, description: str, contact: Dict) -> str:
        restaurant_id = str(uuid.uuid4())
        restaurant_data = {
            'id': restaurant_id,
            'name': name,
            'description': description,
            'contact': contact,
            'menu_id': None,
            'qr_code': None,
            'carbon_calculated': False
        }
        self.restaurants[restaurant_id] = restaurant_data
        st.session_state.restaurants = self.restaurants
        return restaurant_id

    def create_menu(self, restaurant_id: str, categories: Dict) -> str:
        menu_id = str(uuid.uuid4())
        menu_data = {
            'id': menu_id,
            'restaurant_id': restaurant_id,
            'categories': categories,
            'carbon_footprints': {}
        }
        self.menus[menu_id] = menu_data
        st.session_state.menus = self.menus
        self.restaurants[restaurant_id]['menu_id'] = menu_id
        st.session_state.restaurants = self.restaurants
        return menu_id

    def update_menu(self, menu_id: str, categories: Dict):
        """Update existing menu categories"""
        if menu_id in self.menus:
            self.menus[menu_id]['categories'] = categories
            st.session_state.menus = self.menus

    def generate_qr_code(self, restaurant_id: str) -> str:
        menu_url = f"https://menu.committed.app/menu/{restaurant_id}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(menu_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        self.restaurants[restaurant_id]['qr_code'] = qr_code_data
        self.restaurants[restaurant_id]['menu_url'] = menu_url
        st.session_state.restaurants = self.restaurants
        return qr_code_data


class CarbonCalculator:
    def __init__(self):
        self.config = st.session_state.admin_config
        self.emission_factors = self.config['emission_factors']
        self.thresholds = self.config['thresholds']
        self.fixed_emissions = self.config['fixed_emissions']

    def calculate_menu_footprints(self, menu_id: str) -> Dict:
        menu = st.session_state.menus[menu_id]
        footprints = {}

        for category_name, items in menu['categories'].items():
            category_footprints = {}
            for item in items:
                if 'ingredients' in item and item['ingredients']:
                    ingredients = item['ingredients']
                    if isinstance(ingredients, str):
                        ingredients = [ing.strip() for ing in ingredients.split(',') if ing.strip()]
                    footprint = self.calculate_item_footprint(item['name'], ingredients)
                    category_footprints[item['name']] = footprint
            footprints[category_name] = category_footprints

        st.session_state.menus[menu_id]['carbon_footprints'] = footprints
        restaurant_id = menu['restaurant_id']
        st.session_state.restaurants[restaurant_id]['carbon_calculated'] = True
        return footprints

    def calculate_item_footprint(self, item_name: str, ingredients: List[str]) -> Dict:
        breakdown = {
            'ingredients': 0.0,
            'cooking': self.fixed_emissions['cooking'],
            'packaging': self.fixed_emissions['packaging'],
            'customer_travel': self.fixed_emissions['customer_travel']
        }

        for ingredient in ingredients:
            if not ingredient.strip():
                continue
            ingredient_lower = ingredient.lower().strip()
            factor = 1.0  # Default factor for unknown ingredients

            # Find matching emission factor
            for key, emission_factor in self.emission_factors.items():
                if key in ingredient_lower:
                    factor = emission_factor
                    break

            # Assume 100g per ingredient on average
            breakdown['ingredients'] += 0.1 * factor

        total = sum(breakdown.values())
        level, icon = self.get_impact_level(total)

        return {
            'total': round(total, 2),
            'breakdown': breakdown,
            'level': level,
            'icon': icon
        }

    def get_impact_level(self, footprint: float) -> Tuple[str, str]:
        if footprint < self.thresholds['low_impact']:
            return 'Low', '🟢'
        elif footprint < self.thresholds['medium_impact']:
            return 'Medium', '🟡'
        else:
            return 'High', '🔴'


def initialize_session_state():
    """Initialize all session state variables"""
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if 'current_restaurant' not in st.session_state:
        st.session_state.current_restaurant = None


def main():
    # Initialize
    initialize_session_state()
    admin_config = AdminConfig()

    # Header
    st.title("🍽️ Restaurant Management System")
    st.subheader("QR Menu Software + Carbon Footprint Calculator")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📱 QR Menu System")
    with col2:
        st.info("🌱 Carbon Calculator")
    with col3:
        st.info("📊 Analytics Dashboard")

    st.markdown("---")

    # Sidebar navigation
    with st.sidebar:
        st.header("🚀 Navigation")

        if st.session_state.admin_logged_in:
            page_options = ["🏪 Restaurant Management", "📱 Customer Menu Preview", "⚙️ Admin Panel"]
        else:
            page_options = ["🏪 Restaurant Management", "📱 Customer Menu Preview", "🔐 Admin Login"]

        page = st.radio("Select Section:", page_options)

        st.markdown("---")

        # Quick stats
        if st.session_state.restaurants:
            st.subheader("📊 Quick Stats")
            st.metric("Restaurants", len(st.session_state.restaurants))

            menus_count = len([r for r in st.session_state.restaurants.values() if r['menu_id']])
            st.metric("Active Menus", menus_count)

            carbon_count = len([r for r in st.session_state.restaurants.values() if r['carbon_calculated']])
            st.metric("Carbon Calculated", carbon_count)

    # Main content routing
    if page == "🏪 Restaurant Management":
        restaurant_management_page()
    elif page == "📱 Customer Menu Preview":
        customer_menu_preview_page()
    elif page == "🔐 Admin Login":
        admin_login_page()
    elif page == "⚙️ Admin Panel" and st.session_state.admin_logged_in:
        admin_panel_page()

    # Footer
    st.markdown("---")
    st.markdown("**🌱 Powered by committed.app ecosystem**")
    st.caption("Comprehensive Life Cycle Assessment methodology for restaurant sustainability")


def admin_login_page():
    st.header("🔐 Admin Login")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("admin_login"):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                admin_config = AdminConfig()
                if (username == admin_config.default_admin['username'] and
                        admin_config.verify_password(password, admin_config.default_admin['password'])):
                    st.session_state.admin_logged_in = True
                    st.session_state.admin_username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials!")

    with col2:
        st.info("**Demo Credentials:**\n- Username: `admin`\n- Password: `committed123`")


def restaurant_management_page():
    st.header("🏪 Restaurant Management")

    tab1, tab2, tab3 = st.tabs(["🏢 Restaurants", "📋 Menu Builder", "📊 Analytics"])
    restaurant_manager = RestaurantManager()

    with tab1:
        restaurants_tab(restaurant_manager)

    with tab2:
        menu_builder_tab(restaurant_manager)

    with tab3:
        analytics_tab()


def restaurants_tab(restaurant_manager: RestaurantManager):
    st.subheader("Restaurant Profiles")

    # Add new restaurant
    with st.expander("➕ Add New Restaurant", expanded=len(st.session_state.restaurants) == 0):
        with st.form("new_restaurant"):
            col1, col2 = st.columns(2)

            with col1:
                restaurant_name = st.text_input("Restaurant Name*")
                description = st.text_area("Description")
                phone = st.text_input("Phone")

            with col2:
                email = st.text_input("Email")
                address = st.text_area("Address")
                website = st.text_input("Website")

            if st.form_submit_button("🏪 Create Restaurant"):
                if restaurant_name:
                    contact = {'phone': phone, 'email': email, 'address': address, 'website': website}
                    restaurant_id = restaurant_manager.create_restaurant(restaurant_name, description, contact)
                    st.success(f"✅ Restaurant '{restaurant_name}' created!")
                    st.rerun()
                else:
                    st.error("❌ Restaurant name is required!")

    # Display existing restaurants
    if st.session_state.restaurants:
        st.subheader("Your Restaurants")

        for restaurant_id, restaurant in st.session_state.restaurants.items():
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.write(f"**{restaurant['name']}**")
                    st.write(restaurant['description'])
                    st.write(f"📞 {restaurant['contact']['phone']} | 📧 {restaurant['contact']['email']}")

                with col2:
                    menu_status = "✅ Menu Ready" if restaurant['menu_id'] else "⏳ No Menu"
                    carbon_status = "🌱 Carbon Calculated" if restaurant['carbon_calculated'] else "⚠️ No Carbon Data"
                    st.write(f"Status: {menu_status}")
                    st.write(carbon_status)

                with col3:
                    if restaurant['menu_id']:
                        if st.button(f"📱 QR Code", key=f"qr_{restaurant_id}"):
                            qr_data = restaurant_manager.generate_qr_code(restaurant_id)
                            st.session_state.show_qr = restaurant_id
                            st.rerun()

                st.markdown("---")
    else:
        st.info("No restaurants created yet. Add your first restaurant above!")

    # Show QR Code if requested
    display_qr_code()


def display_qr_code():
    """Display QR code if one is selected"""
    if 'show_qr' in st.session_state and st.session_state.show_qr in st.session_state.restaurants:
        restaurant_id = st.session_state.show_qr
        restaurant = st.session_state.restaurants[restaurant_id]

        if 'qr_code' in restaurant:
            st.subheader(f"📱 QR Code for {restaurant['name']}")

            col1, col2 = st.columns([1, 2])

            with col1:
                qr_image = base64.b64decode(restaurant['qr_code'])
                st.image(qr_image, caption="Scan to view menu", width=250)

            with col2:
                st.write(f"**Menu URL:** {restaurant['menu_url']}")
                st.write("**Instructions:**")
                st.write("1. Print this QR code")
                st.write("2. Place on tables or entrance")
                st.write("3. Customers scan to view digital menu")
                st.write("4. Menu shows carbon footprint for each item")

                st.download_button(
                    "📥 Download QR Code",
                    data=base64.b64decode(restaurant['qr_code']),
                    file_name=f"{restaurant['name']}_qr_menu.png",
                    mime="image/png"
                )

            if st.button("❌ Close QR Code"):
                del st.session_state.show_qr
                st.rerun()


def menu_builder_tab(restaurant_manager: RestaurantManager):
    st.subheader("📋 Menu Builder")

    if not st.session_state.restaurants:
        st.warning("⚠️ Please create a restaurant first!")
        return

    # Select restaurant
    restaurant_options = {rid: r['name'] for rid, r in st.session_state.restaurants.items()}
    selected_restaurant_id = st.selectbox(
        "Select Restaurant:",
        options=list(restaurant_options.keys()),
        format_func=lambda x: restaurant_options[x],
        key="menu_builder_restaurant_select"
    )

    if not selected_restaurant_id:
        return

    restaurant = st.session_state.restaurants[selected_restaurant_id]

    # Initialize working categories for this restaurant
    working_categories_key = f"working_categories_{selected_restaurant_id}"

    if working_categories_key not in st.session_state:
        if restaurant['menu_id'] and restaurant['menu_id'] in st.session_state.menus:
            # Load existing menu
            menu = st.session_state.menus[restaurant['menu_id']]
            st.session_state[working_categories_key] = menu['categories'].copy()
        else:
            # Start with empty categories
            st.session_state[working_categories_key] = {}

    # OCR Upload Section
    if OCR_AVAILABLE:
        ocr_upload_section(selected_restaurant_id, working_categories_key)
    else:
        st.info("📸 OCR functionality available after installing: pip install pytesseract opencv-python pillow")

    # Manual Menu Building
    st.subheader("✏️ Manual Menu Building")

    # Add new category - FIXED VERSION
    add_category_section(selected_restaurant_id, working_categories_key)

    # Edit existing categories
    edit_categories_section(selected_restaurant_id, working_categories_key)

    # Save menu buttons
    save_menu_section(restaurant_manager, selected_restaurant_id, working_categories_key, restaurant)


def ocr_upload_section(selected_restaurant_id: str, working_categories_key: str):
    """Handle OCR menu upload"""
    st.subheader("📸 Upload Menu Image (OCR)")

    with st.expander("📤 Upload Menu Photo"):
        st.info("Upload a photo of your paper menu and we'll automatically extract menu items!")

        uploaded_file = st.file_uploader(
            "Choose menu image",
            type=['png', 'jpg', 'jpeg'],
            key=f"menu_upload_{selected_restaurant_id}"
        )

        if uploaded_file is not None:
            process_uploaded_menu_image(uploaded_file, selected_restaurant_id, working_categories_key)


def process_uploaded_menu_image(uploaded_file, selected_restaurant_id: str, working_categories_key: str):
    """Process uploaded menu image with OCR"""
    try:
        image = Image.open(uploaded_file)

        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(image, caption="Uploaded Menu", width=300)

        with col2:
            if st.button("🔍 Extract Menu Items", key=f"extract_ocr_{selected_restaurant_id}"):
                with st.spinner("Processing image and extracting text..."):
                    ocr_processor = MenuOCRProcessor()

                    # Extract text from image
                    extracted_text = ocr_processor.extract_text_from_image(image)

                    if extracted_text.strip():
                        st.success("✅ Text extracted successfully!")

                        # Parse menu items
                        parsed_items = ocr_processor.parse_menu_items(extracted_text)

                        if parsed_items:
                            # Store parsed items in session state
                            st.session_state[f"parsed_items_{selected_restaurant_id}"] = parsed_items
                            st.session_state[f"show_ocr_results_{selected_restaurant_id}"] = True
                            st.rerun()
                        else:
                            st.warning("No menu items detected. Try a clearer image.")
                    else:
                        st.error("❌ Could not extract text from image. Please try a clearer photo.")

    except Exception as e:
        st.error(f"Error processing image: {str(e)}")


def display_ocr_results(selected_restaurant_id: str, working_categories_key: str):
    """Display OCR results for user selection - FIXED VERSION"""
    if f"parsed_items_{selected_restaurant_id}" not in st.session_state:
        return

    parsed_items = st.session_state[f"parsed_items_{selected_restaurant_id}"]

    st.subheader("📋 Detected Menu Items")
    st.info("Select items to add to your menu:")

    # Form to handle OCR item addition
    with st.form(f"ocr_items_form_{selected_restaurant_id}"):
        # Default category for OCR items
        default_category = st.text_input(
            "Category for these items:",
            value="OCR Imported Items"
        )

        selected_items = []

        # Show detected items with checkboxes
        for idx, item in enumerate(parsed_items):
            col_check, col_info = st.columns([1, 4])

            with col_check:
                selected = st.checkbox(
                    "Select",
                    key=f"ocr_item_check_{idx}",
                    value=item['confidence'] > 0.4
                )

            with col_info:
                st.write(f"**{item['name']}**")
                if item['price'] > 0:
                    st.write(f"Price: {item['price']:.2f} ₺")
                if item['ingredients']:
                    st.write(f"Ingredients: {item['ingredients']}")
                st.caption(f"Confidence: {item['confidence']:.0%}")

            if selected:
                selected_items.append(item)

            st.divider()

        # Submit button for the form
        submitted = st.form_submit_button("✅ Add Selected Items to Menu", type="primary")

        if submitted:
            if not default_category or not default_category.strip():
                st.error("❌ Please enter a category name!")
            elif not selected_items:
                st.error("❌ Please select at least one item!")
            else:
                # Ensure category exists in working categories
                if default_category not in st.session_state[working_categories_key]:
                    st.session_state[working_categories_key][default_category] = []

                added_count = 0
                for item in selected_items:
                    # Check if item already exists
                    existing_items = st.session_state[working_categories_key][default_category]
                    if not any(existing['name'].lower() == item['name'].lower() for existing in existing_items):
                        st.session_state[working_categories_key][default_category].append(item)
                        added_count += 1

                if added_count > 0:
                    st.success(f"✅ Added {added_count} items to '{default_category}' category!")
                    # Clear the OCR results
                    if f"parsed_items_{selected_restaurant_id}" in st.session_state:
                        del st.session_state[f"parsed_items_{selected_restaurant_id}"]
                    if f"show_ocr_results_{selected_restaurant_id}" in st.session_state:
                        del st.session_state[f"show_ocr_results_{selected_restaurant_id}"]
                    st.rerun()
                else:
                    st.warning("No new items to add (duplicates detected)")


def add_category_section(selected_restaurant_id: str, working_categories_key: str):
    """Add new category section - FIXED VERSION"""
    with st.expander("➕ Add New Category"):
        # Use form for proper handling
        with st.form(f"add_category_form_{selected_restaurant_id}", clear_on_submit=True):
            new_category_input = st.text_input(
                "Category Name",
                placeholder="e.g., Appetizers, Main Courses, Desserts"
            )

            submitted = st.form_submit_button("Add Category", type="primary")

            if submitted:
                if new_category_input and new_category_input.strip():
                    category_name = new_category_input.strip()

                    if category_name not in st.session_state[working_categories_key]:
                        # Add new category
                        st.session_state[working_categories_key][category_name] = []
                        st.success(f"✅ Category '{category_name}' added!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Category already exists!")
                else:
                    st.error("❌ Please enter a category name!")


def edit_categories_section(selected_restaurant_id: str, working_categories_key: str):
    """Edit existing categories and their items"""
    working_categories = st.session_state[working_categories_key]

    # Show OCR results if available
    if st.session_state.get(f"show_ocr_results_{selected_restaurant_id}", False):
        display_ocr_results(selected_restaurant_id, working_categories_key)
        st.markdown("---")

    if not working_categories:
        st.info("No categories yet. Add your first category above!")
        return

    for category_name in list(working_categories.keys()):
        with st.expander(f"📂 {category_name} ({len(working_categories[category_name])} items)"):

            # Add item to category
            st.write(f"**Add item to {category_name}:**")

            with st.form(f"add_item_form_{category_name}_{selected_restaurant_id}", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    item_name = st.text_input("Item Name*")
                    item_description = st.text_area("Description")
                    item_ingredients = st.text_input("Ingredients (comma-separated)")

                with col2:
                    item_price = st.number_input("Price (₺)*", min_value=0.0, step=0.5)
                    item_vegetarian = st.checkbox("Vegetarian")
                    item_available = st.checkbox("Available", value=True)

                submitted = st.form_submit_button("➕ Add Item", type="secondary")

                if submitted:
                    if item_name.strip() and item_price > 0:
                        new_item = {
                            'name': item_name.strip(),
                            'description': item_description.strip(),
                            'price': item_price,
                            'ingredients': item_ingredients.strip(),
                            'vegetarian': item_vegetarian,
                            'available': item_available
                        }
                        st.session_state[working_categories_key][category_name].append(new_item)
                        st.success(f"✅ '{item_name}' added to {category_name}!")
                        st.rerun()
                    else:
                        st.error("❌ Item name and price are required!")

            # Display existing items
            if working_categories[category_name]:
                st.write(f"**Current items in {category_name}:**")
                for idx, item in enumerate(working_categories[category_name]):
                    col_item, col_action = st.columns([4, 1])

                    with col_item:
                        st.write(f"{idx + 1}. **{item['name']}** - {item['price']:.2f} ₺")
                        if item.get('ingredients'):
                            st.caption(f"Ingredients: {item['ingredients']}")
                        if item.get('vegetarian'):
                            st.caption("🌱 Vegetarian")

                    with col_action:
                        if st.button("🗑️", key=f"del_item_{category_name}_{idx}_{selected_restaurant_id}",
                                     help="Delete item"):
                            st.session_state[working_categories_key][category_name].pop(idx)
                            st.success("Item deleted!")
                            st.rerun()

            # Delete category button
            if st.button(f"🗑️ Delete {category_name}", key=f"del_cat_{category_name}_{selected_restaurant_id}"):
                del st.session_state[working_categories_key][category_name]
                st.success(f"✅ Category '{category_name}' deleted!")
                st.rerun()


def save_menu_section(restaurant_manager: RestaurantManager, selected_restaurant_id: str, working_categories_key: str,
                      restaurant: Dict):
    """Save menu and calculate carbon footprints"""
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Menu", type="primary", key=f"save_menu_{selected_restaurant_id}"):
            working_categories = st.session_state[working_categories_key]
            if working_categories:
                if restaurant['menu_id']:
                    # Update existing menu
                    restaurant_manager.update_menu(restaurant['menu_id'], working_categories)
                else:
                    # Create new menu
                    menu_id = restaurant_manager.create_menu(selected_restaurant_id, working_categories)

                st.success("✅ Menu saved successfully!")
                st.rerun()
            else:
                st.error("❌ Please add at least one category and item!")

    with col2:
        if st.button("🌱 Calculate Carbon Footprints", key=f"calc_carbon_{selected_restaurant_id}"):
            if restaurant['menu_id'] and st.session_state[working_categories_key]:
                # Update menu with current working categories first
                restaurant_manager.update_menu(restaurant['menu_id'], st.session_state[working_categories_key])

                # Calculate carbon footprints
                calculator = CarbonCalculator()
                footprints = calculator.calculate_menu_footprints(restaurant['menu_id'])
                st.success("✅ Carbon footprints calculated!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Please save the menu first!")


def analytics_tab():
    """Analytics dashboard"""
    st.subheader("📊 Restaurant Analytics")

    if not st.session_state.restaurants:
        st.warning("⚠️ No restaurants to analyze!")
        return

    restaurant_options = {rid: r['name'] for rid, r in st.session_state.restaurants.items()}
    selected_restaurant_id = st.selectbox(
        "Select Restaurant:",
        options=list(restaurant_options.keys()),
        format_func=lambda x: restaurant_options[x],
        key="analytics_select"
    )

    if selected_restaurant_id:
        restaurant = st.session_state.restaurants[selected_restaurant_id]

        # Restaurant overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            menu_items_count = 0
            if restaurant['menu_id']:
                menu = st.session_state.menus[restaurant['menu_id']]
                menu_items_count = sum(len(items) for items in menu['categories'].values())
            st.metric("Menu Items", menu_items_count)

        with col2:
            categories_count = 0
            if restaurant['menu_id']:
                categories_count = len(menu['categories'])
            st.metric("Categories", categories_count)

        with col3:
            carbon_status = "Yes" if restaurant['carbon_calculated'] else "No"
            st.metric("Carbon Calculated", carbon_status)

        with col4:
            qr_status = "Yes" if restaurant.get('qr_code') else "No"
            st.metric("QR Code Ready", qr_status)

        # Carbon footprint analysis
        if restaurant['carbon_calculated'] and restaurant['menu_id']:
            display_carbon_analysis(restaurant)
        else:
            st.info("Carbon footprints not calculated yet. Go to Menu Builder to calculate them.")


def display_carbon_analysis(restaurant: Dict):
    """Display detailed carbon footprint analysis"""
    st.subheader("🌱 Carbon Footprint Analysis")

    menu = st.session_state.menus[restaurant['menu_id']]
    footprints = menu.get('carbon_footprints', {})

    if footprints:
        all_items = []
        for category, items in footprints.items():
            for item_name, footprint in items.items():
                all_items.append({
                    'Category': category,
                    'Item': item_name,
                    'Carbon Footprint (kg CO₂e)': footprint['total'],
                    'Impact Level': footprint['level']
                })

        if all_items:
            df = pd.DataFrame(all_items)

            # Summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                avg_footprint = df['Carbon Footprint (kg CO₂e)'].mean()
                st.metric("Average Footprint", f"{avg_footprint:.2f} kg CO₂e")

            with col2:
                low_impact_count = len(df[df['Impact Level'] == 'Low'])
                st.metric("Low Impact Items", f"{low_impact_count}/{len(df)}")

            with col3:
                high_impact_count = len(df[df['Impact Level'] == 'High'])
                st.metric("High Impact Items", f"{high_impact_count}/{len(df)}")

            # Visualizations
            st.subheader("Impact Distribution")
            impact_counts = df['Impact Level'].value_counts()
            st.bar_chart(impact_counts)

            # Top emitters
            st.subheader("Highest Carbon Footprint Items")
            top_emitters = df.nlargest(5, 'Carbon Footprint (kg CO₂e)')
            st.dataframe(top_emitters, use_container_width=True)

            # Detailed data table
            st.subheader("Complete Menu Analysis")
            st.dataframe(df.sort_values('Carbon Footprint (kg CO₂e)', ascending=False), use_container_width=True)

            # Export functionality
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📥 Export Analysis Data",
                data=csv_data,
                file_name=f"{restaurant['name']}_carbon_analysis.csv",
                mime="text/csv"
            )
    else:
        st.info("No carbon footprint data available.")


def customer_menu_preview_page():
    """Customer-facing menu preview"""
    st.header("📱 Customer Menu Preview")

    if not st.session_state.restaurants:
        st.warning("⚠️ No restaurants available!")
        return

    restaurant_options = {rid: r['name'] for rid, r in st.session_state.restaurants.items()}
    selected_restaurant_id = st.selectbox(
        "Select Restaurant:",
        options=list(restaurant_options.keys()),
        format_func=lambda x: restaurant_options[x],
        key="preview_restaurant_select"
    )

    if selected_restaurant_id:
        restaurant = st.session_state.restaurants[selected_restaurant_id]

        # Restaurant header
        st.title(f"🍽️ {restaurant['name']}")
        if restaurant['description']:
            st.write(restaurant['description'])

        # Contact information
        contact = restaurant.get('contact', {})
        if any(contact.values()):
            st.write("📞 " + contact.get('phone', '') + " | 📧 " + contact.get('email', ''))

        if not restaurant['menu_id']:
            st.warning("⚠️ No menu available!")
            return

        menu = st.session_state.menus[restaurant['menu_id']]
        footprints = menu.get('carbon_footprints', {})

        # Display menu categories
        for category_name, items in menu['categories'].items():
            if not items:  # Skip empty categories
                continue

            st.subheader(f"📂 {category_name}")

            for item in items:
                if not item.get('available', True):
                    continue

                display_menu_item(item, category_name, footprints)

                st.markdown("---")


def display_menu_item(item: Dict, category_name: str, footprints: Dict):
    """Display individual menu item with carbon footprint"""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"**{item['name']}**")
        if item.get('description'):
            st.write(f"*{item['description']}*")
        if item.get('ingredients'):
            st.write(f"🥘 Ingredients: {item['ingredients']}")

        # Dietary indicators
        dietary_info = []
        if item.get('vegetarian'):
            dietary_info.append("🌱 Vegetarian")
        if item.get('vegan'):
            dietary_info.append("🌿 Vegan")
        if dietary_info:
            st.write(" | ".join(dietary_info))

    with col2:
        st.write(f"**{item['price']:.2f} ₺**")

        # Carbon footprint display
        if footprints and category_name in footprints and item['name'] in footprints[category_name]:
            footprint_data = footprints[category_name][item['name']]

            if footprint_data['level'] == 'Low':
                color = 'green'
            elif footprint_data['level'] == 'Medium':
                color = 'orange'
            else:
                color = 'red'

            st.write(f":{color}[{footprint_data['icon']} {footprint_data['total']} kg CO₂e]")
            st.caption(f"{footprint_data['level']} Impact")


def admin_panel_page():
    """Admin configuration panel"""
    st.header("⚙️ Admin Panel")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.admin_logged_in = False
            st.rerun()

    with col1:
        st.write(f"Welcome, **{st.session_state.admin_username}**!")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🎯 Thresholds", "📊 System Stats", "🔧 Emission Factors"])

    with tab1:
        configure_thresholds_tab()

    with tab2:
        system_stats_tab()

    with tab3:
        emission_factors_tab()


def configure_thresholds_tab():
    """Configure carbon footprint impact thresholds"""
    st.subheader("Configure Impact Thresholds")

    current_thresholds = st.session_state.admin_config['thresholds']

    col1, col2 = st.columns(2)

    with col1:
        new_low = st.number_input(
            "🟢 Low Impact Threshold (kg CO₂e)",
            min_value=0.1,
            max_value=10.0,
            value=current_thresholds['low_impact'],
            step=0.1
        )
        new_medium = st.number_input(
            "🟡 Medium Impact Threshold (kg CO₂e)",
            min_value=new_low + 0.1,
            max_value=20.0,
            value=current_thresholds['medium_impact'],
            step=0.1
        )

        if st.button("💾 Update Thresholds"):
            st.session_state.admin_config['thresholds']['low_impact'] = new_low
            st.session_state.admin_config['thresholds']['medium_impact'] = new_medium
            st.success("✅ Thresholds updated!")

    with col2:
        st.write("**Current Classification:**")
        st.write(f"- 🟢 Low Impact: 0 - {new_low} kg CO₂e")
        st.write(f"- 🟡 Medium Impact: {new_low} - {new_medium} kg CO₂e")
        st.write(f"- 🔴 High Impact: > {new_medium} kg CO₂e")


def system_stats_tab():
    """Display system statistics"""
    st.subheader("System Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Restaurants", len(st.session_state.restaurants))

    with col2:
        total_menus = len([r for r in st.session_state.restaurants.values() if r['menu_id']])
        st.metric("Active Menus", total_menus)

    with col3:
        carbon_calculated = len([r for r in st.session_state.restaurants.values() if r['carbon_calculated']])
        st.metric("Carbon Calculated", carbon_calculated)

    # Additional system information
    if st.session_state.restaurants:
        st.subheader("Restaurant Details")

        restaurants_data = []
        for rid, restaurant in st.session_state.restaurants.items():
            menu_items = 0
            if restaurant['menu_id'] and restaurant['menu_id'] in st.session_state.menus:
                menu = st.session_state.menus[restaurant['menu_id']]
                menu_items = sum(len(items) for items in menu['categories'].values())

            restaurants_data.append({
                'Restaurant': restaurant['name'],
                'Menu Items': menu_items,
                'Carbon Calculated': '✅' if restaurant['carbon_calculated'] else '❌',
                'QR Code': '✅' if restaurant.get('qr_code') else '❌'
            })

        if restaurants_data:
            df = pd.DataFrame(restaurants_data)
            st.dataframe(df, use_container_width=True)


def emission_factors_tab():
    """Configure emission factors"""
    st.subheader("Emission Factors Configuration")

    st.info("Emission factors are in kg CO₂e per 100g of ingredient")

    current_factors = st.session_state.admin_config['emission_factors']

    # Display current factors in editable form
    col1, col2 = st.columns(2)

    factors_list = list(current_factors.items())
    mid_point = len(factors_list) // 2

    with col1:
        st.write("**Protein & Dairy:**")
        for ingredient, factor in factors_list[:mid_point]:
            new_factor = st.number_input(
                f"{ingredient.title()}",
                value=factor,
                min_value=0.0,
                step=0.1,
                key=f"factor_{ingredient}"
            )
            if new_factor != factor:
                st.session_state.admin_config['emission_factors'][ingredient] = new_factor

    with col2:
        st.write("**Vegetables & Others:**")
        for ingredient, factor in factors_list[mid_point:]:
            new_factor = st.number_input(
                f"{ingredient.title()}",
                value=factor,
                min_value=0.0,
                step=0.1,
                key=f"factor_{ingredient}"
            )
            if new_factor != factor:
                st.session_state.admin_config['emission_factors'][ingredient] = new_factor

    # Add new emission factor
    st.subheader("Add New Emission Factor")
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        new_ingredient = st.text_input("Ingredient Name")

    with col2:
        new_factor = st.number_input("Emission Factor (kg CO₂e/100g)", min_value=0.0, step=0.1)

    with col3:
        st.write("")  # Spacing
        if st.button("Add Factor"):
            if new_ingredient and new_ingredient.lower() not in current_factors:
                st.session_state.admin_config['emission_factors'][new_ingredient.lower()] = new_factor
                st.success(f"Added {new_ingredient}")
                st.rerun()
            elif new_ingredient.lower() in current_factors:
                st.error("Ingredient already exists")
            else:
                st.error("Enter ingredient name")


if __name__ == "__main__":
    main()