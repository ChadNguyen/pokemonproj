from flask import Flask, jsonify, render_template, redirect, flash, url_for
from app import app, db, login_manager
from app.forms import RegisterForm, SignInForm, AddPokemonForm
import requests
from app.models import User, Pokemon
from flask_login import current_user, login_user, logout_user, login_required, UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


@app.route('/poke151')
def poke151():
    response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=151')
    pokemon_list = response.json()['results']
    pokemon_data_list = []  # initialize the list here
    for pokemon in pokemon_list:
        pokemon_data = requests.get(pokemon['url']).json()
        sprite = pokemon_data['sprites']['front_default']
        name = pokemon_data['name'].capitalize()
        description = "No description available."
        if 'flavor_text_entries' in pokemon_data['species']:
            for entry in pokemon_data['species']['flavor_text_entries']:
                if entry['language']['name'] == 'en':
                    description = entry['flavor_text']
                    break
        type = pokemon_data['types'][0]['type']['name'].capitalize()
        hp = pokemon_data['stats'][0]['base_stat']
        attack = pokemon_data['stats'][1]['base_stat']
        defense = pokemon_data['stats'][2]['base_stat']
        sp_attack = pokemon_data['stats'][3]['base_stat']
        sp_defense = pokemon_data['stats'][4]['base_stat']
        speed = pokemon_data['stats'][5]['base_stat']
    
        pokemon_dict = {
            'sprite': sprite,
            'name': name,
            'description': description,
            'type': type,
            'hp': hp,
            'attack': attack,
            'defense': defense,
            'sp_attack': sp_attack,
            'sp_defense': sp_defense,
            'speed': speed
        }
        
        pokemon_data_list.append(pokemon_dict)
    return render_template('poke151.jinja', pokemon_list=pokemon_data_list)



@app.route('/pokemon')
def get_pokemon():
    response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=151')
    pokemon_list = response.json()['results']
    return jsonify(pokemon_list)


@app.route('/pokemon/<string:name_or_id>')
def get_pokemon_by_name_or_id(name_or_id):
    response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{name_or_id}')
    if response.ok:
        pokemon_info = response.json()
        stats = pokemon_info['stats']
        pokemon = {
            'name': pokemon_info['name'],
            'sprite': pokemon_info['sprites']['front_default'],
            'stats': stats
        }
        return jsonify(pokemon)
    else:
        return jsonify({'message': 'Pokemon not found'}), 404



@app.route('/add_pokemon', methods=['GET', 'POST'])
@login_required
def add_pokemon():
    form = AddPokemonForm()
    if form.validate_on_submit():
        name = form.name.data
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{name}')
        if not response.ok:
            flash(f'Could not find Pokemon {name}. Please try again.')
            return redirect('/add_pokemon')
        pokemon_info = response.json()
        front_sprite = pokemon_info['sprites']['front_default']
        types = [type_info['type']['name'] for type_info in pokemon_info['types']]
        pokemon_type = '/'.join(types)
        pokemon = Pokemon(name=name,
                          description='',
                          type=pokemon_type,
                          date_created=datetime.utcnow(),
                          user_id=current_user.id,
                          sprite=front_sprite)
        db.session.add(pokemon)
        db.session.commit()

        flash(f'Pokemon {name} added to your collection!')
        return redirect('/')

    return render_template('add_pokemon.jinja', form=form, add_pokemon_form=form)


# class User(db.Model, UserMixin):
#     def hash_password(self, password):
#         self.password = generate_password(password)

#     def check_password(self, password):
#         return check_password_hash(self.password, password)

@app.route('/collection')
@login_required
def collection():
    pokemon_list = current_user.pokemon.all()
    for pokemon in pokemon_list:
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon.name}')
        if response.ok:
            pokemon_info = response.json()
            stats = pokemon_info['stats']
            pokemon.hp = stats[0]['base_stat']
            pokemon.attack = stats[1]['base_stat']
            pokemon.defense = stats[2]['base_stat']
            pokemon.sp_attack = stats[3]['base_stat']
            pokemon.sp_defense = stats[4]['base_stat']
            pokemon.speed = stats[5]['base_stat']
    return render_template('collection.jinja', pokemon_list=pokemon_list)




@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password)
        u = User(username=username, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('User created successfully!')
        return redirect(url_for('register'))
    return render_template('register.jinja', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = SignInForm()
    if form.validate_on_submit():
        user_match = User.query.filter_by(username=form.username.data).first()
        if user_match is None or not user_match.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user_match, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.jinja', title='Sign In', form=form)



@app.route('/user/<username>')
def show_user(username):
    user_match = User.query.filter_by(username=username).first()
    if not user_match:
        redirect('/')
    posts = user_match.posts
    return render_template('user.jinja', user=user_match, posts=posts)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')



@app.route('/')
def index():
    pokemon_list = Pokemon.query.all()
    return render_template('index.jinja', pokemon_list=pokemon_list, title='Pokemon Index')



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


