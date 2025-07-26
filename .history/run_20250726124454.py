from app import app

if __name__ == '__main__':
    # Run the Flask app on all network interfaces (0.0.0.0) 
    # so it can be accessed from other machines/containers
    app.run(host='0.0.0.0', port=5000, debug=True) 