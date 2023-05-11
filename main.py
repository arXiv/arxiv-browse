from browse.factory import create_web_app

if __name__ == "__main__":
    app = create_web_app()
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['DEBUG'] = True
    app.run(debug=True)
