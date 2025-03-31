from flask import Flask, request, Response, render_template, flash, jsonify, session, redirect, url_for
from flask_session import Session
from dotenv import load_dotenv
import os
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
import urllib.parse

# Load environment variables
load_dotenv()

# Ensure API Key is Loaded
mistral_api_key = os.getenv("MISTRAL_API_KEY")
if not mistral_api_key:
    raise ValueError("MISTRAL API Key is missing! Check your environment variables.")

# Initialize Mistral AI Model
model = ChatMistralAI(model="mistral-large-latest", api_key=mistral_api_key)

# Initialize Flask app
app = Flask(__name__)

# Encode MongoDB password safely
password = urllib.parse.quote_plus("Rajeev@1")  # Ensure password is properly encoded
username = "rajeev22joshi"  

app.config["MONGO_URI"] = (
    f"mongodb+srv://{username}:{password}@bot.spvioop.mongodb.net/BoT"
    "?retryWrites=true&w=majority&appName=BoT"
)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secret")

# Initialize MongoDB
mongo = PyMongo(app)

# Session configuration
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Chatbot Workflow
workflow = StateGraph(state_schema=MessagesState)

def call_model(state: MessagesState):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Kindly help the user."),
        MessagesPlaceholder(variable_name="messages")
    ])
    prompt = prompt_template.invoke(state)
    try:
        response = model.invoke(prompt)
        return {"messages": response}
    except Exception as e:
        return {"messages": [SystemMessage(content=f"Error: {str(e)}")]}

workflow.add_node("model", call_model)
workflow.add_edge(START, "model")

memory = MemorySaver()
chatbot_engine = workflow.compile(checkpointer=memory)  

@app.route("/")
def index():
    form = RegistrationForm()
    return render_template("register.html", form=form)

@app.route("/register", methods=["GET", "POST"])  
def register():
    form = RegistrationForm()
    if request.method == "POST" and form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        existing_user = mongo.db.users.find_one({"$or": [{"username": username}, {"email": email}]})

        if existing_user:
            flash("Email already registered!", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one({"username": username, "email": email, "password": hashed_password})

        session["loggedin"] = True
        session["username"] = username

        flash("Registration successful! Welcome, " + username, "success")
        return redirect(url_for("chatbot"))
    
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = mongo.db.users.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["loggedin"] = True
            session["username"] = user["username"]

            flash("Login successful!", "success")
            return redirect(url_for("chatbot"))  
        else:
            flash("Incorrect email or password", "error")  
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

@app.route("/chat", methods=["GET", "POST"])
def chatbot():
    if not session.get("loggedin"):
        flash("Unauthorized access! Please log in first.", "error")
        return redirect(url_for("login"))

    user_id = session["username"]

    if request.method == "GET":
        return render_template("index.html")

    user_input = request.json.get("message", "")
    if not user_input:
        return Response("No input provided.", status=400)

    input_messages = [HumanMessage(content=user_input)]
    config = {"thread_id": f"user_{user_id}"}

    def stream_response():
        response_text = ""
        for chunk, metadata in chatbot_engine.stream({"messages": input_messages}, config=config, stream_mode="messages"):
            if isinstance(chunk, AIMessage):
                response_text += chunk.content
                yield chunk.content  
    return Response(stream_response(), content_type="text/event-stream")

@app.route("/contact")
def contact():
    return redirect("https://rajeevs-portfolio-six.vercel.app")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))


    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Default Render port is 10000
    app.run(host="0.0.0.0", port=port, debug=False)
    #app.run(host="0.0.0.0", port=8080)
