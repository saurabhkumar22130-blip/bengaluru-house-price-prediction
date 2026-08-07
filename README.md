# Premium Real Estate Engine

A modern, highly interactive Real Estate and Price Prediction platform built with a sleek glassmorphism aesthetic. This project simulates an industry-level real estate dashboard complete with an interactive map, procedural property generation, machine learning price prediction templates, and an AI chat assistant.

## ✨ Key Features

- **Procedural Map Engine**: Uses Leaflet.js and OpenStreetMap with a custom procedural generation algorithm. Instead of static mock data, properties are dynamically generated based on GPS coordinates. This ensures that a specific location on the map will consistently yield the exact same property, simulating a massive global real estate database without needing a paid API key.
- **Stock Market Analytics**: Each property features localized market trend data. Clicking on the market trend badge opens a beautiful Chart.js line graph showing a 12-month simulated price trajectory.
- **AI Agent Integration**: Every property on the map has a dedicated virtual AI assistant. Users can ask the agent for the property's rent, visit schedule, or the broker's direct contact number.
- **Machine Learning Price Predictor**: Users can input property details (Location, BHK, Sqft, Bathrooms) to get an instant price prediction.
- **User Profiles & Saved Properties**: Users can save properties directly from the map or save their price predictions. These are stored using client-side `localStorage` and dynamically rendered in a dedicated Profile page with empty-state handling.
- **Premium UI/UX**: Designed using TailwindCSS with a focus on micro-animations, glassmorphism, soft shadows, and a clean, modern typography system (Inter & Manrope).

## 🛠️ Technology Stack

- **Backend**: Python, Flask, Pandas, Scikit-Learn (Model template)
- **Frontend**: HTML5, Vanilla JavaScript, TailwindCSS (via CDN)
- **Mapping**: Leaflet.js, OpenStreetMap
- **Data Visualization**: Chart.js
- **Icons & Fonts**: Google Material Symbols, Google Fonts

## 🚀 Setup Instructions

1. **Prerequisites**: Ensure you have Python 3.8+ installed on your system.
2. **Install Dependencies**:
   Open your terminal and install the required Python packages:
   ```bash
   pip install flask pandas scikit-learn
   ```
3. **Run the Application**:
   Navigate to the project folder and run the Flask server:
   ```bash
   python main.py
   ```
4. **Access the App**:
   Open your browser and go to `http://127.0.0.1:5000`

## 📁 Project Structure

- `main.py`: The Flask backend routing and procedural data generation engine.
- `model.pkl`: The exported machine learning model for price prediction.
- `templates/`
  - `login.html`: The authentication portal.
  - `index.html`: The landing page with the price prediction form.
  - `predict.html`: The prediction results page with options to save.
  - `map.html`: The interactive map, AI chat, and stock chart interface.
  - `profile.html`: The user dashboard for managing saved properties and predictions.

## 🔮 Future Roadmap (Industry-Level Upgrades)
To take this prototype to production, consider the following upgrades:
- Implement a real database (PostgreSQL/SQLAlchemy) to replace `localStorage`.
- Integrate secure JWT authentication or OAuth.
- Connect the AI Chat to a real LLM (like OpenAI GPT-4 or Google Gemini).
- Swap the procedural generation for a paid real-estate API (like Google Places or Zillow).
