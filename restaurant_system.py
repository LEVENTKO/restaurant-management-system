import streamlit as st
import pandas as pd
import qrcode
from PIL import Image
import io
import base64
import json
import datetime
import re
from typing import List, Dict, Tuple
import uuid
import numpy as np
import random

# Page configuration
st.set_page_config(
    page_title="Restaurant Sales & Marketing System",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B35, #F7931E);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #FF6B35;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    .info-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'restaurants' not in st.session_state:
        st.session_state.restaurants = []
    if 'menu_items' not in st.session_state:
        st.session_state.menu_items = []
    if 'categories' not in st.session_state:
        st.session_state.categories = ['Appetizers', 'Main Course', 'Desserts', 'Beverages', 'Soups', 'Salads']
    if 'orders' not in st.session_state:
        st.session_state.orders = []
    if 'customers' not in st.session_state:
        st.session_state.customers = []
    if 'marketing_campaigns' not in st.session_state:
        st.session_state.marketing_campaigns = []
    if 'sales_data' not in st.session_state:
        st.session_state.sales_data = []
    if 'customer_feedback' not in st.session_state:
        st.session_state.customer_feedback = []


# Restaurant Management Functions
def add_restaurant():
    """Add a new restaurant"""
    st.subheader("🏪 Add New Restaurant")

    with st.form("add_restaurant_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Restaurant Name*")
            cuisine_type = st.selectbox("Cuisine Type",
                                        ["Italian", "Chinese", "Indian", "Mexican", "American", "Mediterranean",
                                         "Japanese", "Thai", "French", "Other"])
            address = st.text_area("Address")

        with col2:
            phone = st.text_input("Phone Number")
            email = st.text_input("Email")
            manager_name = st.text_input("Manager Name")

        operating_hours = st.text_input("Operating Hours (e.g., 9:00 AM - 10:00 PM)")
        capacity = st.number_input("Seating Capacity", min_value=1, value=50)

        submitted = st.form_submit_button("Add Restaurant")

        if submitted and name:
            restaurant = {
                'id': str(uuid.uuid4()),
                'name': name,
                'cuisine_type': cuisine_type,
                'address': address,
                'phone': phone,
                'email': email,
                'manager_name': manager_name,
                'operating_hours': operating_hours,
                'capacity': capacity,
                'created_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            st.session_state.restaurants.append(restaurant)
            st.success(f"✅ Restaurant '{name}' added successfully!")
            st.rerun()


def view_restaurants():
    """View and manage restaurants"""
    st.subheader("🏪 Restaurant Management")

    if not st.session_state.restaurants:
        st.info("📝 No restaurants added yet. Add your first restaurant!")
        return

    # Display restaurants in a nice format
    for i, restaurant in enumerate(st.session_state.restaurants):
        with st.expander(f"🏪 {restaurant['name']} - {restaurant['cuisine_type']}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Manager:** {restaurant.get('manager_name', 'N/A')}")
                st.write(f"**Phone:** {restaurant.get('phone', 'N/A')}")
                st.write(f"**Email:** {restaurant.get('email', 'N/A')}")

            with col2:
                st.write(f"**Address:** {restaurant.get('address', 'N/A')}")
                st.write(f"**Hours:** {restaurant.get('operating_hours', 'N/A')}")
                st.write(f"**Capacity:** {restaurant.get('capacity', 'N/A')} seats")

            with col3:
                st.write(f"**Created:** {restaurant.get('created_date', 'N/A')}")
                if st.button(f"Delete {restaurant['name']}", key=f"del_restaurant_{i}"):
                    st.session_state.restaurants.pop(i)
                    st.rerun()


# Menu Management Functions
def add_menu_item():
    """Add menu item manually"""
    st.subheader("📋 Add Menu Item")

    if not st.session_state.restaurants:
        st.warning("⚠️ Please add a restaurant first!")
        return

    # Manual Menu Item Entry
    st.markdown("### ✏️ Add New Menu Item")

    with st.form("add_menu_item_form"):
        col1, col2 = st.columns(2)

        with col1:
            restaurant_options = [r['name'] for r in st.session_state.restaurants]
            selected_restaurant = st.selectbox("Restaurant", restaurant_options)
            item_name = st.text_input("Item Name*")
            category = st.selectbox("Category", st.session_state.categories)
            price = st.number_input("Price ($)", min_value=0.0, step=0.50)

        with col2:
            ingredients = st.text_area("Ingredients (comma separated)")
            is_vegetarian = st.checkbox("Vegetarian")
            is_vegan = st.checkbox("Vegan")
            carbon_footprint = st.number_input("Carbon Footprint (kg CO₂e)", min_value=0.0, step=0.1)

        description = st.text_area("Description")

        # Bulk add section
        st.markdown("### 📝 Bulk Add Items")
        bulk_items = st.text_area(
            "Add multiple items (one per line, format: Item Name, Price)",
            placeholder="Margherita Pizza, 12.99\nCaesar Salad, 8.99\nPasta Carbonara, 14.99",
            height=100
        )

        submitted = st.form_submit_button("Add Menu Item(s)")

        if submitted:
            items_added = 0

            # Add single item
            if item_name:
                ingredients_list = [ing.strip() for ing in ingredients.split(',') if ing.strip()]

                menu_item = {
                    'id': str(uuid.uuid4()),
                    'restaurant_name': selected_restaurant,
                    'item_name': item_name,
                    'category': category,
                    'price': price,
                    'ingredients': ingredients_list,
                    'description': description,
                    'carbon_footprint': carbon_footprint,
                    'is_vegetarian': is_vegetarian,
                    'is_vegan': is_vegan,
                    'created_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'source': 'Manual'
                }

                st.session_state.menu_items.append(menu_item)
                items_added += 1

            # Add bulk items
            if bulk_items:
                lines = bulk_items.strip().split('\n')
                for line in lines:
                    if ',' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            try:
                                price_val = float(parts[1].strip())

                                bulk_menu_item = {
                                    'id': str(uuid.uuid4()),
                                    'restaurant_name': selected_restaurant,
                                    'item_name': name,
                                    'category': 'Other',
                                    'price': price_val,
                                    'ingredients': [],
                                    'description': '',
                                    'carbon_footprint': 0.0,
                                    'is_vegetarian': False,
                                    'is_vegan': False,
                                    'created_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'source': 'Bulk'
                                }

                                st.session_state.menu_items.append(bulk_menu_item)
                                items_added += 1
                            except ValueError:
                                st.warning(f"Invalid price format in line: {line}")

            if items_added > 0:
                st.success(f"✅ Added {items_added} menu item(s) successfully!")
                st.rerun()
            else:
                st.warning("Please enter at least one menu item.")


def view_menu():
    """View and manage menu items"""
    st.subheader("📋 Menu Management")

    if not st.session_state.menu_items:
        st.info("📝 No menu items added yet. Add your first menu item!")
        return

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        restaurants = list(set([item['restaurant_name'] for item in st.session_state.menu_items]))
        restaurant_filter = st.selectbox("Filter by Restaurant", ['All'] + restaurants)

    with col2:
        categories = list(set([item['category'] for item in st.session_state.menu_items]))
        category_filter = st.selectbox("Filter by Category", ['All'] + categories)

    with col3:
        search_term = st.text_input("Search items")

    # Filter menu items
    filtered_items = st.session_state.menu_items

    if restaurant_filter != 'All':
        filtered_items = [item for item in filtered_items if item['restaurant_name'] == restaurant_filter]

    if category_filter != 'All':
        filtered_items = [item for item in filtered_items if item['category'] == category_filter]

    if search_term:
        filtered_items = [item for item in filtered_items if search_term.lower() in item['item_name'].lower()]

    # Display menu items
    if filtered_items:
        for i, item in enumerate(filtered_items):
            with st.expander(f"🍽️ {item['item_name']} - ${item['price']:.2f}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Restaurant:** {item['restaurant_name']}")
                    st.write(f"**Category:** {item['category']}")
                    st.write(f"**Price:** ${item['price']:.2f}")

                with col2:
                    st.write(f"**Carbon Footprint:** {item['carbon_footprint']:.2f} kg CO₂e")
                    veg_status = "🌱 Vegetarian" if item.get('is_vegetarian') else ""
                    vegan_status = "🌿 Vegan" if item.get('is_vegan') else ""
                    if veg_status or vegan_status:
                        st.write(f"{veg_status} {vegan_status}")

                with col3:
                    st.write(f"**Source:** {item.get('source', 'Unknown')}")
                    st.write(f"**Created:** {item['created_date']}")

                if item.get('ingredients'):
                    st.write(f"**Ingredients:** {', '.join(item['ingredients'])}")

                if item.get('description'):
                    st.write(f"**Description:** {item['description']}")

                if st.button(f"Delete {item['item_name']}", key=f"del_item_{item['id']}"):
                    st.session_state.menu_items = [mi for mi in st.session_state.menu_items if mi['id'] != item['id']]
                    st.rerun()
    else:
        st.info("No menu items match your filters.")


# Sales Management Functions
def sales_dashboard():
    """Sales analytics dashboard"""
    st.subheader("📊 Sales Dashboard")

    # Generate sample sales data if empty
    if not st.session_state.sales_data:
        generate_sample_sales_data()

    # Sales metrics
    col1, col2, col3, col4 = st.columns(4)

    total_sales = sum([sale['amount'] for sale in st.session_state.sales_data])
    total_orders = len(st.session_state.sales_data)
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0

    with col1:
        st.metric("💰 Total Sales", f"${total_sales:,.2f}")

    with col2:
        st.metric("📦 Total Orders", f"{total_orders:,}")

    with col3:
        st.metric("💵 Avg Order Value", f"${avg_order_value:.2f}")

    with col4:
        # Calculate growth (mock calculation)
        growth = 15.5  # Mock growth percentage
        st.metric("📈 Growth", f"{growth}%", delta=f"{growth}%")

    st.markdown("---")

    # Sales chart
    if st.session_state.sales_data:
        df = pd.DataFrame(st.session_state.sales_data)
        df['date'] = pd.to_datetime(df['date'])

        # Daily sales
        daily_sales = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
        daily_sales.columns = ['Date', 'Sales']

        st.subheader("📈 Daily Sales Trend")
        st.line_chart(daily_sales.set_index('Date'))

        # Top selling items
        if 'item_name' in df.columns:
            st.subheader("🏆 Top Selling Items")
            top_items = df.groupby('item_name')['quantity'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_items)


def generate_sample_sales_data():
    """Generate sample sales data for demonstration"""
    sample_data = []

    # Get some menu items for realistic data
    menu_items = st.session_state.menu_items
    if not menu_items:
        # Create some default items
        menu_items = [
            {'item_name': 'Margherita Pizza', 'price': 12.99},
            {'item_name': 'Caesar Salad', 'price': 8.99},
            {'item_name': 'Pasta Carbonara', 'price': 14.99},
            {'item_name': 'Grilled Chicken', 'price': 16.99},
            {'item_name': 'Chocolate Cake', 'price': 6.99}
        ]

    # Generate 30 days of sample data
    for i in range(30):
        date = datetime.datetime.now() - datetime.timedelta(days=i)

        # Random number of orders per day
        orders_per_day = random.randint(5, 25)

        for _ in range(orders_per_day):
            item = random.choice(menu_items)
            quantity = random.randint(1, 3)

            sale = {
                'id': str(uuid.uuid4()),
                'date': date.strftime("%Y-%m-%d"),
                'item_name': item['item_name'],
                'quantity': quantity,
                'price': item['price'],
                'amount': item['price'] * quantity,
                'restaurant_name': st.session_state.restaurants[0][
                    'name'] if st.session_state.restaurants else 'Demo Restaurant'
            }

            sample_data.append(sale)

    st.session_state.sales_data = sample_data


# Marketing Functions
def marketing_campaigns():
    """Marketing campaign management"""
    st.subheader("📢 Marketing Campaigns")

    tab1, tab2, tab3 = st.tabs(["📝 Create Campaign", "📊 Active Campaigns", "📈 Performance"])

    with tab1:
        st.markdown("### Create New Marketing Campaign")

        with st.form("marketing_campaign_form"):
            campaign_name = st.text_input("Campaign Name*")
            campaign_type = st.selectbox("Campaign Type",
                                         ["Email Marketing", "Social Media", "SMS", "Push Notification",
                                          "Discount Offer", "Loyalty Program"])

            col1, col2 = st.columns(2)

            with col1:
                target_audience = st.multiselect("Target Audience",
                                                 ["All Customers", "New Customers", "Returning Customers",
                                                  "VIP Customers", "Inactive Customers"])
                start_date = st.date_input("Start Date")
                budget = st.number_input("Budget ($)", min_value=0.0, step=50.0)

            with col2:
                channel = st.selectbox("Channel", ["Email", "SMS", "Social Media", "In-App", "Website Banner"])
                end_date = st.date_input("End Date")
                expected_reach = st.number_input("Expected Reach", min_value=0, step=100)

            message = st.text_area("Campaign Message")
            offer_details = st.text_area("Offer Details (if applicable)")

            submitted = st.form_submit_button("🚀 Launch Campaign")

            if submitted and campaign_name:
                campaign = {
                    'id': str(uuid.uuid4()),
                    'name': campaign_name,
                    'type': campaign_type,
                    'target_audience': target_audience,
                    'channel': channel,
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    'end_date': end_date.strftime("%Y-%m-%d"),
                    'budget': budget,
                    'expected_reach': expected_reach,
                    'message': message,
                    'offer_details': offer_details,
                    'status': 'Active',
                    'created_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'impressions': 0,
                    'clicks': 0,
                    'conversions': 0
                }

                st.session_state.marketing_campaigns.append(campaign)
                st.success(f"✅ Campaign '{campaign_name}' launched successfully!")
                st.rerun()

    with tab2:
        if st.session_state.marketing_campaigns:
            for campaign in st.session_state.marketing_campaigns:
                with st.expander(f"📢 {campaign['name']} - {campaign['status']}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Type:** {campaign['type']}")
                        st.write(f"**Channel:** {campaign['channel']}")
                        st.write(f"**Budget:** ${campaign['budget']:.2f}")

                    with col2:
                        st.write(f"**Start Date:** {campaign['start_date']}")
                        st.write(f"**End Date:** {campaign['end_date']}")
                        st.write(f"**Expected Reach:** {campaign['expected_reach']:,}")

                    with col3:
                        st.write(f"**Status:** {campaign['status']}")
                        st.write(f"**Created:** {campaign['created_date']}")

                    if campaign['message']:
                        st.write(f"**Message:** {campaign['message']}")

                    if campaign['offer_details']:
                        st.write(f"**Offer:** {campaign['offer_details']}")
        else:
            st.info("No marketing campaigns created yet.")

    with tab3:
        st.markdown("### Campaign Performance Analytics")

        if st.session_state.marketing_campaigns:
            # Generate mock performance data
            performance_data = []
            for campaign in st.session_state.marketing_campaigns:
                # Mock data - in real app this would come from actual analytics
                impressions = np.random.randint(1000, 10000)
                clicks = np.random.randint(50, impressions // 10)
                conversions = np.random.randint(5, clicks // 5)

                performance_data.append({
                    'Campaign': campaign['name'],
                    'Impressions': impressions,
                    'Clicks': clicks,
                    'Conversions': conversions,
                    'CTR': f"{(clicks / impressions * 100):.2f}%",
                    'Conversion Rate': f"{(conversions / clicks * 100):.2f}%",
                    'Cost': f"${campaign['budget']:.2f}"
                })

            df = pd.DataFrame(performance_data)
            st.dataframe(df, use_container_width=True)

            # Performance charts
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("👁️ Impressions by Campaign")
                chart_data = df.set_index('Campaign')['Impressions']
                st.bar_chart(chart_data)

            with col2:
                st.subheader("🎯 Conversions by Campaign")
                chart_data = df.set_index('Campaign')['Conversions']
                st.bar_chart(chart_data)
        else:
            st.info("No campaign performance data available.")


# Customer Management Functions
def customer_management():
    """Customer relationship management"""
    st.subheader("👥 Customer Management")

    tab1, tab2, tab3 = st.tabs(["📊 Customer Analytics", "👤 Customer Database", "💌 Customer Communication"])

    with tab1:
        # Generate sample customer data if empty
        if not st.session_state.customers:
            generate_sample_customer_data()

        # Customer metrics
        col1, col2, col3, col4 = st.columns(4)

        total_customers = len(st.session_state.customers)
        new_customers = len([c for c in st.session_state.customers if c.get('is_new', False)])
        avg_orders = sum([c.get('total_orders', 0) for c in
                          st.session_state.customers]) / total_customers if total_customers > 0 else 0
        avg_value = sum([c.get('lifetime_value', 0) for c in
                         st.session_state.customers]) / total_customers if total_customers > 0 else 0

        with col1:
            st.metric("👥 Total Customers", f"{total_customers:,}")

        with col2:
            st.metric("🆕 New Customers", f"{new_customers:,}")

        with col3:
            st.metric("📦 Avg Orders/Customer", f"{avg_orders:.1f}")

        with col4:
            st.metric("💰 Avg Lifetime Value", f"${avg_value:.2f}")

        # Customer segmentation
        if st.session_state.customers:
            st.subheader("📊 Customer Segmentation")

            # Segment by order frequency
            segments = {'New': 0, 'Regular': 0, 'VIP': 0, 'Inactive': 0}

            for customer in st.session_state.customers:
                orders = customer.get('total_orders', 0)
                if orders == 0:
                    segments['Inactive'] += 1
                elif orders <= 2:
                    segments['New'] += 1
                elif orders <= 10:
                    segments['Regular'] += 1
                else:
                    segments['VIP'] += 1

            segment_df = pd.DataFrame(list(segments.items()), columns=['Segment', 'Count'])
            st.bar_chart(segment_df.set_index('Segment'))

    with tab2:
        st.markdown("### Customer Database")

        if st.session_state.customers:
            # Search and filter
            col1, col2 = st.columns(2)

            with col1:
                search_customer = st.text_input("🔍 Search customers")

            with col2:
                segment_filter = st.selectbox("Filter by Segment", ['All', 'New', 'Regular', 'VIP', 'Inactive'])

            # Display customers
            filtered_customers = st.session_state.customers

            if search_customer:
                filtered_customers = [c for c in filtered_customers if search_customer.lower() in c['name'].lower()]

            for customer in filtered_customers[:10]:  # Show first 10
                with st.expander(f"👤 {customer['name']} - {customer.get('email', 'No email')}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Phone:** {customer.get('phone', 'N/A')}")
                        st.write(f"**Total Orders:** {customer.get('total_orders', 0)}")

                    with col2:
                        st.write(f"**Lifetime Value:** ${customer.get('lifetime_value', 0):.2f}")
                        st.write(f"**Last Order:** {customer.get('last_order_date', 'Never')}")

                    with col3:
                        st.write(f"**Preferred Restaurant:** {customer.get('preferred_restaurant', 'N/A')}")
                        st.write(f"**Customer Since:** {customer.get('join_date', 'N/A')}")
        else:
            st.info("No customer data available.")

    with tab3:
        st.markdown("### Customer Communication")

        # Email templates
        st.subheader("📧 Email Templates")

        template_type = st.selectbox("Select Template Type",
                                     ["Welcome Email", "Order Confirmation", "Promotional Offer", "Birthday Discount",
                                      "Feedback Request"])

        if template_type == "Welcome Email":
            st.text_area("Template",
                         "Welcome to [Restaurant Name]! 🎉\n\nThank you for joining our family. We're excited to serve you delicious meals.\n\nEnjoy 10% off your first order with code: WELCOME10\n\nBest regards,\n[Restaurant Team]",
                         height=150)

        elif template_type == "Promotional Offer":
            st.text_area("Template",
                         "🍕 Special Offer Just for You!\n\nGet 20% off your next order this weekend only!\n\nUse code: WEEKEND20\n\nOrder now: [Order Link]\n\nOffer valid until Sunday 11:59 PM",
                         height=150)

        # Bulk email sending simulation
        st.subheader("📤 Send Bulk Email")

        target_group = st.selectbox("Target Group",
                                    ["All Customers", "New Customers", "Regular Customers", "VIP Customers"])
        email_subject = st.text_input("Email Subject")

        if st.button("📧 Send Email"):
            target_count = len(st.session_state.customers)  # Simplified
            st.success(f"✅ Email sent to {target_count} customers in '{target_group}' group!")


def generate_sample_customer_data():
    """Generate sample customer data"""
    sample_customers = []
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Chris", "Emma", "Alex", "Maria"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
                  "Martinez"]

    for i in range(50):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"

        customer = {
            'id': str(uuid.uuid4()),
            'name': name,
            'email': f"{name.lower().replace(' ', '.')}@email.com",
            'phone': f"+1-{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'total_orders': random.randint(0, 25),
            'lifetime_value': random.uniform(50, 1000),
            'is_new': random.choice([True, False]),
            'join_date': (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365))).strftime(
                "%Y-%m-%d"),
            'last_order_date': (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).strftime(
                "%Y-%m-%d"),
            'preferred_restaurant': st.session_state.restaurants[0][
                'name'] if st.session_state.restaurants else 'Demo Restaurant'
        }

        sample_customers.append(customer)

    st.session_state.customers = sample_customers


# QR Code Generator
def generate_qr_code():
    """Generate QR codes for restaurants"""
    st.subheader("📱 QR Code Generator")

    if not st.session_state.restaurants:
        st.warning("⚠️ Please add a restaurant first!")
        return

    restaurant_options = [r['name'] for r in st.session_state.restaurants]
    selected_restaurant = st.selectbox("Select Restaurant", restaurant_options)

    # QR Code options
    qr_type = st.selectbox("QR Code Type", ["Menu", "Website", "Contact Info", "Feedback Form"])

    if qr_type == "Menu":
        url = f"https://menu.restaurant-app.com/{selected_restaurant.lower().replace(' ', '-')}"
    elif qr_type == "Website":
        url = st.text_input("Website URL", "https://your-restaurant-website.com")
    elif qr_type == "Contact Info":
        restaurant = next(r for r in st.session_state.restaurants if r['name'] == selected_restaurant)
        url = f"tel:{restaurant.get('phone', '')}"
    else:  # Feedback Form
        url = f"https://feedback.restaurant-app.com/{selected_restaurant.lower().replace(' ', '-')}"

    if st.button("🔗 Generate QR Code"):
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(url)
            qr.make(fit=True)

            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Display QR code
            st.image(qr_image, caption=f"QR Code for {selected_restaurant}", width=300)

            # Download button
            img_buffer = io.BytesIO()
            qr_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            st.download_button(
                label="📥 Download QR Code",
                data=img_buffer,
                file_name=f"{selected_restaurant}_{qr_type}_QR.png",
                mime="image/png"
            )

            st.success(f"✅ QR Code generated for {selected_restaurant}!")

        except Exception as e:
            st.error(f"Error generating QR code: {str(e)}")


# Feedback Management
def feedback_management():
    """Customer feedback and review management"""
    st.subheader("💬 Customer Feedback")

    tab1, tab2, tab3 = st.tabs(["📝 Feedback Form", "⭐ Reviews", "📊 Analytics"])

    with tab1:
        st.markdown("### Customer Feedback Form")

        with st.form("feedback_form"):
            col1, col2 = st.columns(2)

            with col1:
                customer_name = st.text_input("Name (Optional)")
                customer_email = st.text_input("Email (Optional)")
                restaurant = st.selectbox("Restaurant", [r['name'] for r in
                                                         st.session_state.restaurants] if st.session_state.restaurants else [
                    'Demo Restaurant'])

            with col2:
                visit_date = st.date_input("Visit Date")
                rating = st.select_slider("Overall Rating", options=[1, 2, 3, 4, 5], value=5,
                                          format_func=lambda x: "⭐" * x)
                order_type = st.selectbox("Order Type", ["Dine-in", "Takeout", "Delivery"])

            # Detailed ratings
            st.markdown("#### Detailed Ratings")
            col1, col2, col3 = st.columns(3)

            with col1:
                food_rating = st.select_slider("Food Quality", options=[1, 2, 3, 4, 5], value=5,
                                               format_func=lambda x: "⭐" * x)

            with col2:
                service_rating = st.select_slider("Service", options=[1, 2, 3, 4, 5], value=5,
                                                  format_func=lambda x: "⭐" * x)

            with col3:
                atmosphere_rating = st.select_slider("Atmosphere", options=[1, 2, 3, 4, 5], value=5,
                                                     format_func=lambda x: "⭐" * x)

            comments = st.text_area("Comments and Suggestions")

            submitted = st.form_submit_button("📝 Submit Feedback")

            if submitted:
                feedback = {
                    'id': str(uuid.uuid4()),
                    'customer_name': customer_name or 'Anonymous',
                    'customer_email': customer_email,
                    'restaurant': restaurant,
                    'visit_date': visit_date.strftime("%Y-%m-%d"),
                    'overall_rating': rating,
                    'food_rating': food_rating,
                    'service_rating': service_rating,
                    'atmosphere_rating': atmosphere_rating,
                    'order_type': order_type,
                    'comments': comments,
                    'submitted_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                st.session_state.customer_feedback.append(feedback)
                st.success("✅ Thank you for your feedback!")
                st.rerun()

    with tab2:
        if st.session_state.customer_feedback:
            st.markdown("### Recent Reviews")

            for feedback in st.session_state.customer_feedback[-10:]:  # Show last 10
                with st.expander(
                        f"⭐ {feedback['overall_rating']}/5 - {feedback['customer_name']} - {feedback['visit_date']}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Restaurant:** {feedback['restaurant']}")
                        st.write(f"**Order Type:** {feedback['order_type']}")
                        st.write(f"**Overall Rating:** {'⭐' * feedback['overall_rating']}")

                    with col2:
                        st.write(f"**Food:** {'⭐' * feedback['food_rating']}")
                        st.write(f"**Service:** {'⭐' * feedback['service_rating']}")
                        st.write(f"**Atmosphere:** {'⭐' * feedback['atmosphere_rating']}")

                    if feedback['comments']:
                        st.write(f"**Comments:** {feedback['comments']}")
        else:
            st.info("No feedback received yet.")

    with tab3:
        if st.session_state.customer_feedback:
            st.markdown("### Feedback Analytics")

            df = pd.DataFrame(st.session_state.customer_feedback)

            # Overall metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                avg_rating = df['overall_rating'].mean()
                st.metric("📊 Average Rating", f"{avg_rating:.1f}/5")

            with col2:
                total_feedback = len(df)
                st.metric("💬 Total Feedback", f"{total_feedback}")

            with col3:
                positive_feedback = len(df[df['overall_rating'] >= 4])
                positive_rate = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
                st.metric("👍 Positive Rate", f"{positive_rate:.1f}%")

            with col4:
                recent_feedback = len(
                    df[pd.to_datetime(df['submitted_date']) >= (datetime.datetime.now() - datetime.timedelta(days=7))])
                st.metric("📅 This Week", f"{recent_feedback}")

            # Rating distribution
            st.subheader("⭐ Rating Distribution")
            rating_counts = df['overall_rating'].value_counts().sort_index()
            st.bar_chart(rating_counts)

            # Category ratings
            st.subheader("📊 Category Ratings")
            category_avg = pd.DataFrame({
                'Food': [df['food_rating'].mean()],
                'Service': [df['service_rating'].mean()],
                'Atmosphere': [df['atmosphere_rating'].mean()]
            })
            st.bar_chart(category_avg.T)
        else:
            st.info("No feedback data available for analytics.")


# Main Application
def main():
    """Main application function"""
    initialize_session_state()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🍕 Restaurant Sales & Marketing System</h1>
        <p>Complete solution for restaurant management, sales tracking, and marketing automation</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")

    pages = {
        "🏠 Dashboard": "dashboard",
        "🏪 Restaurant Management": "restaurants",
        "📋 Menu Management": "menu",
        "📊 Sales Analytics": "sales",
        "📢 Marketing Campaigns": "marketing",
        "👥 Customer Management": "customers",
        "📱 QR Code Generator": "qr_codes",
        "💬 Customer Feedback": "feedback"
    }

    selected_page = st.sidebar.radio("Select Page", list(pages.keys()))
    page_key = pages[selected_page]

    # Page routing
    if page_key == "dashboard":
        dashboard()
    elif page_key == "restaurants":
        restaurant_management_page()
    elif page_key == "menu":
        menu_management_page()
    elif page_key == "sales":
        sales_dashboard()
    elif page_key == "marketing":
        marketing_campaigns()
    elif page_key == "customers":
        customer_management()
    elif page_key == "qr_codes":
        generate_qr_code()
    elif page_key == "feedback":
        feedback_management()


def dashboard():
    """Main dashboard with overview metrics"""
    st.subheader("📊 Dashboard Overview")

    # Quick metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        restaurant_count = len(st.session_state.restaurants)
        st.metric("🏪 Restaurants", restaurant_count)

    with col2:
        menu_count = len(st.session_state.menu_items)
        st.metric("🍽️ Menu Items", menu_count)

    with col3:
        customer_count = len(st.session_state.customers)
        st.metric("👥 Customers", customer_count)

    with col4:
        campaign_count = len(st.session_state.marketing_campaigns)
        st.metric("📢 Campaigns", campaign_count)

    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ Add Restaurant", use_container_width=True):
            st.session_state.current_page = "restaurants"
            st.rerun()

    with col2:
        if st.button("📋 Add Menu Item", use_container_width=True):
            st.session_state.current_page = "menu"
            st.rerun()

    with col3:
        if st.button("📢 Create Campaign", use_container_width=True):
            st.session_state.current_page = "marketing"
            st.rerun()

    # Recent activity
    st.markdown("---")
    st.subheader("📈 Recent Activity")

    if st.session_state.menu_items:
        st.write("**Recent Menu Items:**")
        for item in st.session_state.menu_items[-3:]:
            st.write(f"• {item['item_name']} at {item['restaurant_name']}")

    if st.session_state.marketing_campaigns:
        st.write("**Active Campaigns:**")
        for campaign in st.session_state.marketing_campaigns[-3:]:
            st.write(f"• {campaign['name']} - {campaign['type']}")


def restaurant_management_page():
    """Restaurant management page"""
    tab1, tab2 = st.tabs(["➕ Add Restaurant", "🏪 View Restaurants"])

    with tab1:
        add_restaurant()

    with tab2:
        view_restaurants()


def menu_management_page():
    """Menu management page"""
    tab1, tab2 = st.tabs(["➕ Add Menu Item", "📋 View Menu"])

    with tab1:
        add_menu_item()

    with tab2:
        view_menu()


if __name__ == "__main__":
    main()