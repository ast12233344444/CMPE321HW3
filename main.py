from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import database_calls as db # Importing the database call functions
from datetime import datetime # Added for date parsing/formatting

from database_calls import get_matches_assigned_to_arbiter

app = Flask(__name__)
app.secret_key = 'supersecretkey_dev123' # Using a more specific secret key

# --- Database Configuration ---
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password', # User-provided password
    'db': 'HW3',             # User-provided database name
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True # Ensure changes are committed
}

def get_db_connection():
    try:
        conn = pymysql.connect(**db_config)
        return conn
    except pymysql.Error as e:
        # Log this error properly in a real application
        print(f"Error connecting to MySQL Database: {e}")
        # Optionally, flash a message to the user or handle appropriately
        flash("Database connection error. Please try again later or contact support.", "danger")
        return None


# --- Routes ---
@app.route('/')
def index():
    if 'username' in session:
        role = session.get('role')
        if role == 'db_manager':
            return redirect(url_for('db_manager_dashboard'))
        elif role == 'coach':
            return redirect(url_for('coach_dashboard'))
        elif role == 'player':
            return redirect(url_for('player_dashboard'))
        elif role == 'arbiter':
            return redirect(url_for('arbiter_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            # Error already flashed by get_db_connection
            return render_template('login.html', error='Database connection failed.')

        user_data = None
        role = None
        
        # Try logging in as DBManager
        auth_result = db.log_in_dbmanager(username, password, conn)
        if auth_result.get("status") == 200:
            user_data = auth_result.get("user_data")
            role = "db_manager"
        
        # If not DBManager, try Player
        if not user_data:
            auth_result = db.log_in_player(username, password, conn)
            if auth_result.get("status") == 200:
                user_data = auth_result.get("user_data")
                role = "player"

        # If not Player, try Coach
        if not user_data:
            auth_result = db.log_in_coach(username, password, conn)
            if auth_result.get("status") == 200:
                user_data = auth_result.get("user_data")
                role = "coach"
        
        # If not Coach, try Arbiter
        if not user_data:
            auth_result = db.log_in_arbiter(username, password, conn)
            if auth_result.get("status") == 200:
                user_data = auth_result.get("user_data")
                role = "arbiter"
        
        conn.close()

        if user_data and role:
            session['username'] = user_data['username']
            session['role'] = role
            session['name'] = user_data.get('name', user_data['username']) # Assuming 'name' field exists
            
            # Store role-specific info if needed, e.g., team_name for coach
            if role == 'coach':
                # We need to fetch the coach's current team name.
                # This might require an additional DB call or be part of user_data from log_in_coach
                # For now, using a placeholder or assuming it's in user_data
                session['team_name'] = user_data.get('team_name', 'N/A') 
                # The schema has Manages(coach_username, team_id). We'd need to query Team for team_name.
                # Let's assume for now log_in_coach might be modified to return this or we add a call.

            flash('Login successful!', 'success')
            if role == 'db_manager':
                return redirect(url_for('db_manager_dashboard'))
            elif role == 'coach':
                return redirect(url_for('coach_dashboard'))
            elif role == 'player':
                return redirect(url_for('player_dashboard'))
            elif role == 'arbiter':
                return redirect(url_for('arbiter_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return render_template('login.html', error='Invalid username or password.')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Dashboard Routes ---
@app.route('/db_manager_dashboard')
def db_manager_dashboard():
    if 'username' not in session or session.get('role') != 'db_manager':
        flash('Please log in as a Database Manager.', 'warning')
        return redirect(url_for('login'))
    return render_template('db_manager_dashboard.html', username=session.get('name'))

@app.route('/coach_dashboard')
def coach_dashboard():
    if 'username' not in session or session.get('role') != 'coach':
        flash('Please log in as a Coach.', 'warning')
        return redirect(url_for('login'))
    
    coach_username = session['username']
    coach_name = session.get('name', coach_username)
    team_info = None
    coach_matches = []

    conn = get_db_connection()
    if conn:
        try:
            coach_team_result = db.get_coach_current_team(coach_username, conn)
            if coach_team_result.get("status") == 200 and coach_team_result.get("team"):
                team_info = coach_team_result.get("team")
                matches_result = db.get_matches_involving_coach_team(team_info["team_id"], conn)
                if matches_result.get("status") == 200:
                    coach_matches = matches_result.get("matches")
                else:
                    flash(matches_result.get("message", "Could not fetch coach's matches."), "danger")
            else:
                flash(coach_team_result.get("message", "Could not determine coach's current team."), "warning")
        except Exception as e:
            flash(f"Error fetching coach dashboard data: {str(e)}", "danger")
        finally:
            conn.close()
    
    team_name_display = team_info["team_name"] if team_info else "N/A"

    return render_template('coach_dashboard.html', username=coach_name, team_name=team_name_display, matches=coach_matches)

@app.route('/player_dashboard')
def player_dashboard():
    if 'username' not in session or session.get('role') != 'player':
        flash('Please log in as a Player.', 'warning')
        return redirect(url_for('login'))
    
    player_username = session['username']
    player_name = session.get('name', player_username)
    match_history_data = []

    conn = get_db_connection()
    if conn:
        try:
            history_result = db.get_player_match_history_detailed(player_username, conn)
            print(history_result)
            if history_result.get("status") == 200:
                match_history_data = history_result.get("match_history")
            else:
                flash(history_result.get("message", "Could not fetch match history."), "danger")
        except Exception as e:
            flash(f"Error fetching match history: {str(e)}", "danger")
        finally:
            conn.close()
            
    return render_template('player_dashboard.html', username=player_name, match_history=match_history_data)

@app.route('/arbiter_dashboard')
def arbiter_dashboard():
    if 'username' not in session or session.get('role') != 'arbiter':
        flash('Please log in as an Arbiter.', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    assigned_matches_data = []
    if conn:
        try:
            arbiter_username = session['username']
            matches_result = db.get_detailed_matches_for_arbiter(arbiter_username, conn)
            get_matches_assigned_to_arbiter(arbiter_username, conn)
            if matches_result.get("status") == 200:
                assigned_matches_data = matches_result.get("detailed_matches")
                print(assigned_matches_data)
            else:
                flash(matches_result.get("message", "Could not fetch assigned matches."), "danger")
        except Exception as e:
            flash(f"Error fetching assigned matches: {str(e)}", "danger")
        finally:
            conn.close()
    
    return render_template('arbiter_dashboard.html', username=session.get('name'), assigned_matches=assigned_matches_data)

# --- DB Manager Function Routes (Placeholders - to be integrated with db_calls) ---
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'username' not in session or session.get('role') != 'db_manager':
        return redirect(url_for('login'))
    if request.method == 'POST':
        conn = get_db_connection()
        if not conn:
            return render_template('add_user.html', error='Database connection failed.')

        role = request.form['role']
        params = {
            'username': request.form['username'],
            'password': request.form['password'],
            'name': request.form['name'],
            'surname': request.form['surname'],
            'nationality': request.form['nationality']
        }
        result = None
        try:
            if role == 'player':
                dob_form = request.form['date_of_birth'] # DD-MM-YYYY
                # Convert DD-MM-YYYY to MM/DD/YY for strptime %D
                try:
                    dt_obj = datetime.strptime(dob_form, "%d-%m-%Y")
                    dob_for_db_calls = dt_obj.strftime("%m/%d/%y") # %D format
                except ValueError:
                    flash("Invalid date format for Date of Birth. Please use DD-MM-YYYY.", "danger")
                    return redirect(url_for('add_user'))

                params.update({
                    'date_of_birth': dob_for_db_calls, # Pass MM/DD/YY string
                    'fide_id': request.form['fide_id'],
                    'elo_rating': int(request.form['elo_rating']),
                    'title_id': request.form.get('title_id') # Optional
                })
                print("player params: ", params)
                result = db.register_player(params, conn)
            elif role == 'coach':
                contract_start_form = request.form['contract_start_coach'] # DD-MM-YYYY
                contract_end_form = request.form['contract_end_coach'] # DD-MM-YYYY
                try:
                    cs_dt_obj = datetime.strptime(contract_start_form, "%d-%m-%Y")
                    cs_for_db_calls = cs_dt_obj.strftime("%m/%d/%y")
                    ce_dt_obj = datetime.strptime(contract_end_form, "%d-%m-%Y")
                    ce_for_db_calls = ce_dt_obj.strftime("%m/%d/%y")
                except ValueError:
                    flash("Invalid date format for contract dates. Please use DD-MM-YYYY.", "danger")
                    return redirect(url_for('add_user'))

                params.update({
                    'team_id': int(request.form['team_id_coach']),
                    'contract_start': cs_for_db_calls,
                    'contract_end': ce_for_db_calls,
                    # Certifications are handled separately if needed, not by register_coach
                })
                print("coach params: ", params)
                result = db.register_coach(params, conn)
            elif role == 'arbiter':
                params.update({
                    'experience_level': request.form['experience_level'],
                    # 'certifications_arbiter': request.form.get('certifications_arbiter') # Not in db.register_arbiter
                })
                print("arbiter params: ", params)
                result = db.register_arbiter(params, conn)

            if result and result.get("status") == 200:
                flash(f"User {params['username']} ({role}) added successfully!", 'success')
            elif result:
                flash(f"Error adding user: {result.get('message')}", 'danger')
            else:
                flash(f"User creation for role '{role}' not fully implemented or failed.", 'warning')

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
        finally:
            conn.close()
        return redirect(url_for('db_manager_dashboard'))
    
    # GET request: Populate dropdowns for Player (titles) and Coach (teams)
    all_titles = []
    all_teams = []
    conn_get = get_db_connection()
    if conn_get:
        try:
            titles_result = db.get_all_titles(conn_get)
            if titles_result.get("status") == 200:
                all_titles = titles_result.get("titles", [])
            
            teams_result = db.get_all_teams(conn_get)
            if teams_result.get("status") == 200:
                all_teams = teams_result.get("teams", [])
        except Exception as e:
            flash(f"Error fetching data for add user form: {str(e)}", "danger")
        finally:
            conn_get.close()
            
    return render_template('add_user.html', all_titles=all_titles, all_teams=all_teams)

@app.route('/rename_hall', methods=['GET', 'POST'])
def rename_hall():
    if 'username' not in session or session.get('role') != 'db_manager':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    halls_list = []
    if conn:
        try:
            # Assuming a function get_all_halls() exists in database_calls.py that returns list of dicts
            # halls_list = db.get_all_halls(conn) # The existing one takes username, which is odd for all halls.
            # Let's assume a generic one or adapt.
            # For now, using the one from database_calls, though it seems for coach.
             if hasattr(db, 'get_all_halls'): # Check if function exists
                halls_list = db.get_all_halls(session['username'], conn)["halls"] # Pass username as it expects

        finally:
            conn.close()
    
    if not halls_list: # Fallback if DB call fails or returns empty
        halls_list = [{'hall_id': 1, 'hall_name': 'Main Hall (Mock)'}, {'hall_id': 2, 'hall_name': 'Side Hall (Mock)'}]


    if request.method == 'POST':
        hall_id_to_rename = request.form.get('hall_id')
        new_hall_name = request.form.get('new_hall_name')

        if not hall_id_to_rename or not new_hall_name:
            flash("Hall ID and new name are required.", "warning")
            return redirect(url_for('rename_hall'))
        
        conn_rename = get_db_connection()
        if not conn_rename:
            # flash already handled by get_db_connection
            return redirect(url_for('rename_hall'))
        
        try:
            hall_id_int = int(hall_id_to_rename)
            result = db.rename_hall_by_id(hall_id_int, new_hall_name, conn_rename)
            if result and result.get("status") == 200:
                flash(result.get("message"), 'success')
            elif result:
                flash(result.get("message"), 'danger')
            else:
                flash("An unexpected error occurred during hall renaming.", 'danger')
        except ValueError:
            flash("Invalid Hall ID format.", "danger")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "danger")
        finally:
            if conn_rename:
                conn_rename.close()
        return redirect(url_for('db_manager_dashboard'))
        
    return render_template('rename_hall.html', halls=halls_list)


# --- Coach Function Routes (Placeholders) ---
# ... (Other routes will be integrated similarly, focusing on login and basic dashboards first)
@app.route('/create_match', methods=['GET', 'POST'])
def create_match():
    if 'username' not in session or session.get('role') != 'coach':
        flash("Please log in as a Coach.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        # flash handled by get_db_connection
        return redirect(url_for('coach_dashboard'))

    coach_username = session['username']
    form_data = {
        "coach_team": None,
        "all_halls": [],
        "all_tables_with_hall_info": [],
        "opponent_teams": [],
        "certified_arbiters": []
    }

    try:
        coach_team_result = db.get_coach_current_team(coach_username, conn)
        if coach_team_result.get("status") == 200:
            form_data["coach_team"] = coach_team_result.get("team")
        else:
            flash(coach_team_result.get("message", "Could not fetch coach's team."), "danger")
            # Allow to proceed but coach_team will be None, template should handle

        halls_result = db.get_all_halls(coach_username, conn) # username still passed as per old signature
        if halls_result.get("status") == 200:
            form_data["all_halls"] = halls_result.get("halls")

        tables_result = db.get_all_tables_with_hall_info(conn)
        if tables_result.get("status") == 200:
            form_data["all_tables_with_hall_info"] = tables_result.get("tables_with_hall_info")
        
        teams_result = db.get_all_teams(conn)
        if teams_result.get("status") == 200:
            # Filter out the coach's own team from opponent teams list
            if form_data["coach_team"]:
                coach_team_id = form_data["coach_team"]["team_id"]
                form_data["opponent_teams"] = [t for t in teams_result.get("teams", []) if t["team_id"] != coach_team_id]
            else:
                form_data["opponent_teams"] = teams_result.get("teams", [])
        
        arbiters_result = db.get_all_certified_arbiters(conn)
        if arbiters_result.get("status") == 200:
            form_data["certified_arbiters"] = arbiters_result.get("arbiters")

    except Exception as e:
        flash(f"Error fetching data for match creation form: {str(e)}", "danger")
    finally:
        conn.close()

    if request.method == 'POST':
        try:
            match_date_str = request.form.get('match_date')
            time_slot_str = request.form.get('time_slot')
            hall_id_str = request.form.get('hall_id')
            # The table_id from the form might be just table_id, or composite like "hall_id-table_id"
            # Assuming create_match.html sends table_id directly for now.
            # If it sends a composite, parsing will be needed.
            # The `all_tables_with_hall_info` provides `table_id` and `hall_id` separately.
            # The form should ideally submit `table_id` and the `hall_id` for that table.
            # For now, let's assume the form has separate select for hall and then table,
            # and table_id submitted is unique for that hall or globally unique if schema allows.
            # The `Tables` PK is (table_id, hall_id). So we need both.
            # Let's assume the form for 'table_id' actually submits a value that IS the table_id
            # and the hall_id is from its own dropdown.
            table_id_str = request.form.get('table_id')
            opponent_team_id_str = request.form.get('opponent_team_id')
            arbiter_username = request.form.get('arbiter_username')
            
            if not form_data.get("coach_team") or not form_data["coach_team"].get("team_id"):
                flash("Could not identify coach's team. Please try again.", "danger")
                return redirect(url_for('create_match'))
            coach_team_id = form_data["coach_team"]["team_id"]

            # Basic validation
            if not all([match_date_str, time_slot_str, hall_id_str, table_id_str, opponent_team_id_str, arbiter_username]):
                flash("All fields are required for creating a match.", "warning")
                return render_template('create_match.html', **form_data) # Re-render with existing form data

            # Convert and validate data types
            match_date_obj = datetime.strptime(match_date_str, "%d-%m-%Y")
            match_date_db = match_date_obj.strftime("%Y-%m-%d")
            time_slot = int(time_slot_str)
            hall_id = int(hall_id_str)
            table_id = int(table_id_str) # This table_id must correspond to the selected hall_id
            opponent_team_id = int(opponent_team_id_str)

            if coach_team_id == opponent_team_id:
                flash("Coach's team cannot play against itself.", "warning")
                return render_template('create_match.html', **form_data)

            match_details = {
                'date': match_date_db,
                'time_slot': time_slot,
                'hall_id': hall_id,
                'table_id': table_id,
                'team1_id': coach_team_id,
                'team2_id': opponent_team_id,
                'arbiter_username': arbiter_username,
                'creator': coach_username
            }
            
            # Re-establish connection for POST, as the one from GET is closed.
            conn_post = get_db_connection()
            if not conn_post:
                return redirect(url_for('coach_dashboard')) # Flash handled by get_db_connection

            try:
                creation_result = db.create_new_match(match_details, conn_post)
                if creation_result.get("status") == 200:
                    flash(creation_result.get("message"), "success")
                    return redirect(url_for('coach_dashboard'))
                else:
                    flash(creation_result.get("message", "Failed to create match."), "danger")
            finally:
                conn_post.close()
            
            # If creation failed, re-render form with originally fetched data
            return render_template('create_match.html', **form_data)

        except ValueError as ve:
            flash(f"Invalid data submitted: {str(ve)}. Please check your inputs.", "danger")
            return render_template('create_match.html', **form_data) # Re-render
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "danger")
            return redirect(url_for('create_match')) # Redirect to clear form state on major error
        
    return render_template('create_match.html', **form_data)

@app.route('/assign_player_to_match', methods=['GET', 'POST'])
def assign_player_to_match():
    if 'username' not in session or session.get('role') != 'coach':
        flash("Please log in as a Coach.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('coach_dashboard'))

    coach_username = session['username']
    form_data = {
        "matches_needing_assignment": [],
        "team_players": []
    }

    try:
        coach_team_result = db.get_coach_current_team(coach_username, conn)
        if coach_team_result.get("status") == 200 and coach_team_result.get("team"):
            coach_team_id = coach_team_result["team"]["team_id"]
            
            matches_result = db.get_coach_matches_needing_assignment(coach_team_id, conn)
            if matches_result.get("status") == 200:
                form_data["matches_needing_assignment"] = matches_result.get("matches_needing_assignment")

            players_result = db.get_players_for_team(coach_team_id, conn)
            if players_result.get("status") == 200:
                form_data["team_players"] = players_result.get("players")
        else:
            flash(coach_team_result.get("message", "Could not determine coach's current team."), "warning")

    except Exception as e:
        flash(f"Error fetching data for player assignment: {str(e)}", "danger")
    finally:
        conn.close()

    if request.method == 'POST':
        coach_username_post = session.get('username') # For re-fetching coach_team_id if needed
        match_id_str = request.form.get('match_id')
        player_username_to_assign = request.form.get('player_username')

        if not match_id_str or not player_username_to_assign:
            flash("Match ID and Player Username are required for assignment.", "warning")
            # Re-populate form_data for re-rendering
            conn_reget = get_db_connection()
            if conn_reget:
                try:
                    coach_team_res = db.get_coach_current_team(coach_username_post, conn_reget)
                    if coach_team_res.get("status") == 200 and coach_team_res.get("team"):
                        coach_team_id_reget = coach_team_res["team"]["team_id"]
                        matches_res = db.get_coach_matches_needing_assignment(coach_team_id_reget, conn_reget)
                        form_data["matches_needing_assignment"] = matches_res.get("matches_needing_assignment", [])
                        players_res = db.get_players_for_team(coach_team_id_reget, conn_reget)
                        form_data["team_players"] = players_res.get("players", [])
                finally:
                    conn_reget.close()
            return render_template('assign_player_to_match.html', **form_data)

        conn_post = get_db_connection()
        if not conn_post:
            return redirect(url_for('coach_dashboard'))

        try:
            match_id = int(match_id_str)
            
            # Fetch coach's team ID again to ensure it's current for the POST request context
            coach_team_info_post = db.get_coach_current_team(coach_username_post, conn_post)
            if not (coach_team_info_post.get("status") == 200 and coach_team_info_post.get("team")):
                flash(coach_team_info_post.get("message", "Could not verify coach's team for assignment."), "danger")
                # Re-populate form_data for re-rendering (similar to above block)
                # This part can be refactored into a helper if it gets too repetitive
                return redirect(url_for('assign_player_to_match')) # Simplified redirect

            assigning_coach_team_id = coach_team_info_post["team"]["team_id"]

            assignment_result = db.assign_player_to_match_db(match_id, player_username_to_assign, assigning_coach_team_id, conn_post)

            if assignment_result.get("status") == 200:
                flash(assignment_result.get("message"), "success")
                return redirect(url_for('coach_dashboard'))
            else:
                flash(assignment_result.get("message", "Failed to assign player."), "danger")
        
        except ValueError:
            flash("Invalid Match ID.", "danger")
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "danger")
        finally:
            conn_post.close()
        
        # If failed, re-populate form data and re-render
        # This requires re-fetching data as conn from GET is closed.
        conn_repopulate = get_db_connection()
        if conn_repopulate:
            try:
                coach_team_repopulate_res = db.get_coach_current_team(coach_username_post, conn_repopulate)
                if coach_team_repopulate_res.get("status") == 200 and coach_team_repopulate_res.get("team"):
                    coach_team_id_repopulate = coach_team_repopulate_res["team"]["team_id"]
                    matches_repopulate_res = db.get_coach_matches_needing_assignment(coach_team_id_repopulate, conn_repopulate)
                    form_data["matches_needing_assignment"] = matches_repopulate_res.get("matches_needing_assignment", [])
                    players_repopulate_res = db.get_players_for_team(coach_team_id_repopulate, conn_repopulate)
                    form_data["team_players"] = players_repopulate_res.get("players", [])
            finally:
                conn_repopulate.close()
        return render_template('assign_player_to_match.html', **form_data)
        
    return render_template('assign_player_to_match.html', **form_data)

@app.route('/delete_match', methods=['GET', 'POST'])
def delete_match():
    if 'username' not in session or session.get('role') != 'coach':
        flash("Please log in as a Coach.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        return redirect(url_for('coach_dashboard'))

    coach_username = session['username']
    coach_team_matches = []

    try:
        coach_team_result = db.get_coach_current_team(coach_username, conn)
        if coach_team_result.get("status") == 200 and coach_team_result.get("team"):
            coach_team_id = coach_team_result["team"]["team_id"]
            
            matches_result = db.get_matches_involving_coach_team(coach_team_id, conn)
            if matches_result.get("status") == 200:
                coach_team_matches = matches_result.get("matches")
                matches_created_by_coach = []
                for match in coach_team_matches:
                    if match["Creator"] == coach_username:
                        matches_created_by_coach.append(match)
                coach_team_matches = matches_created_by_coach
        else:
            flash(coach_team_result.get("message", "Could not determine coach's current team."), "warning")

    except Exception as e:
        flash(f"Error fetching matches for deletion: {str(e)}", "danger")
    finally:
        conn.close()

    if request.method == 'POST':
        match_id_to_delete_str = request.form.get('match_id')
        coach_username_post = session.get('username')

        if not match_id_to_delete_str:
            flash("Match ID is required for deletion.", "warning")
            return redirect(url_for('delete_match')) # Re-render GET

        conn_post = get_db_connection()
        if not conn_post:
            return redirect(url_for('coach_dashboard'))

        try:
            match_id = int(match_id_to_delete_str)
            
            coach_team_info_post = db.get_coach_current_team(coach_username_post, conn_post)
            if not (coach_team_info_post.get("status") == 200 and coach_team_info_post.get("team")):
                flash(coach_team_info_post.get("message", "Could not verify coach's team for deletion."), "danger")
                return redirect(url_for('delete_match'))
            
            coach_team_id = coach_team_info_post["team"]["team_id"]
            
            deletion_result = db.delete_match_by_id_for_coach(match_id, coach_team_id, conn_post)
            
            if deletion_result.get("status") == 200:
                flash(deletion_result.get("message"), "success")
            else:
                flash(deletion_result.get("message", "Failed to delete match."), "danger")
            
            return redirect(url_for('coach_dashboard'))

        except ValueError:
            flash("Invalid Match ID format.", "danger")
        except Exception as e:
            flash(f"An unexpected error occurred during match deletion: {str(e)}", "danger")
        finally:
            if conn_post: # Ensure conn_post is defined before trying to close
                conn_post.close()
        
        # If error, redirect to the delete_match page to show updated list
        return redirect(url_for('delete_match'))
        
    return render_template('delete_match.html', coach_team_matches=coach_team_matches)

@app.route('/view_halls_coach')
def view_halls_coach():
    if 'username' not in session or session.get('role') != 'coach':
        return redirect(url_for('login'))
    halls_list = []
    conn = get_db_connection()
    if conn:
        try:
            if hasattr(db, 'get_all_halls'):
                 halls_result = db.get_all_halls(session['username'], conn) # username is unused by current db.get_all_halls
                 if halls_result.get("status") == 200:
                     halls_list = halls_result.get("halls", [])
                 else:
                     flash(halls_result.get("message", "Could not fetch hall information."), "danger")
            else:
                flash("Hall information service is unavailable.", "warning")
        except Exception as e:
            flash(f"Error fetching hall information: {str(e)}", "danger")
        finally:
            conn.close()
    return render_template('view_halls_coach.html', halls=halls_list)


# --- Arbiter Function Routes (Placeholders) ---
@app.route('/submit_rating', methods=['GET', 'POST'])
def submit_rating():
    if 'username' not in session or session.get('role') != 'arbiter':
        flash("Please log in as an Arbiter.", "warning")
        return redirect(url_for('login'))

    arbiter_username = session['username']
    unrated_matches_data = []
    conn = get_db_connection()

    if conn:
        try:
            matches_result = db.get_unrated_past_matches_for_arbiter(arbiter_username, conn)
            if matches_result.get("status") == 200:
                unrated_matches_data = matches_result.get("unrated_matches")
            else:
                flash(matches_result.get("message", "Could not fetch matches for rating."), "danger")
        except Exception as e:
            flash(f"Error fetching matches for rating: {str(e)}", "danger")
        finally:
            conn.close()

    if request.method == 'POST':
        match_id_str = request.form.get('match_id')
        rating_value_str = request.form.get('rating_value')
        arbiter_username_session = session.get('username')

        if not match_id_str or not rating_value_str:
            flash("Match ID and Rating are required.", "warning")
            return redirect(url_for('submit_rating')) # Re-render GET

        conn_post = get_db_connection()
        if not conn_post:
            return redirect(url_for('arbiter_dashboard'))

        try:
            match_id = int(match_id_str)
            rating_value = int(rating_value_str)

            submission_result = db.submit_match_rating_db(match_id, arbiter_username_session, rating_value, conn_post)

            if submission_result.get("status") == 200:
                flash(submission_result.get("message"), "success")
            else:
                flash(submission_result.get("message", "Failed to submit rating."), "danger")
            
            return redirect(url_for('arbiter_dashboard'))

        except ValueError:
            flash("Invalid Match ID or Rating value. Rating must be an integer.", "danger")
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "danger")
        finally:
            if conn_post:
                conn_post.close()
        
        return redirect(url_for('submit_rating')) # Re-render GET if error during POST processing
        
    return render_template('submit_rating.html', unrated_matches=unrated_matches_data)

@app.route('/view_arbiter_stats')
def view_arbiter_stats():
    if 'username' not in session or session.get('role') != 'arbiter':
        return redirect(url_for('login'))
    stats_data = {"total_rated_matches": 0, "average_rating": 0.0}
    conn = get_db_connection()
    if conn:
        try:
            if hasattr(db, 'get_avg_n_count_ratings_arbiters'):
                avg_rating, num_rating = db.get_avg_n_count_ratings_arbiters(session['username'], conn)
                stats_data = {"total_rated_matches": num_rating, "average_rating": avg_rating}
        finally:
            conn.close()
    return render_template('view_arbiter_stats.html', stats=stats_data)


# --- Player Function Routes (Placeholders) ---
@app.route('/view_co_player_stats')
def view_co_player_stats():
    if 'username' not in session or session.get('role') != 'player':
        return redirect(url_for('login'))
    
    opponents_list = []
    most_frequent_stats = None
    conn = get_db_connection()
    if conn:
        try:
            if hasattr(db, 'get_player_past_matched_players') and hasattr(db, 'get_most_played_players_w_elo'):
                # This gets usernames. We need full opponent details (name, surname, elo) for the first list.
                # The current get_player_past_matched_players only returns usernames.
                # This part needs adjustment in database_calls.py or more complex logic here.
                # For now, let's assume we can get some basic info.
                
                # opponent_usernames = db.get_player_past_matched_players(session['username'], conn)
                # For each username, fetch details (N+1 problem).
                # A better function in db_calls would be get_opponent_details_for_player.
                
                # For most frequent:
                # result_most_freq = db.get_most_played_players_w_elo(session['username'], conn)
                # This returns [(username, elo_rating)]. We need to format it for the template.
                # The template expects:
                # most_frequent_opponent_stats: {
                # opponents_info: [{name, surname, games_played}, ...],
                # elo_rating_metric: avg_elo or single_elo
                # }
                # This also requires more processing or a refined db_call.
                pass # Using mock data for now
        finally:
            conn.close()
            
    opponents_list = []
    most_frequent_stats = None # This will be implemented next

    conn = get_db_connection()
    if conn:
        try:
            player_username = session['username']
            
            # Fetch detailed opponent history (Requirement 5a)
            opponents_result = db.get_detailed_opponent_history(player_username, conn)
            if opponents_result.get("status") == 200:
                opponents_list = opponents_result.get("opponents")
            else:
                flash(opponents_result.get("message", "Could not fetch opponent history."), "danger")

            # Fetch and process most frequent opponent stats (Requirement 5b)
            most_played_result = db.get_most_played_players_w_elo(player_username, conn)
            
            if most_played_result: # Directly returns the list of dicts or an empty list
                if len(most_played_result) == 1:
                    opponent = most_played_result[0]
                    most_frequent_stats = {
                        "opponents_info": [{
                            "name": opponent["name"],
                            "surname": opponent["surname"],
                            # "games_played": max_occurrence - this info is not directly returned by get_most_played_players_w_elo
                            # The function would need modification to return games_played count if needed for display.
                            # For now, we just know they are the "most played".
                        }],
                        "elo_rating_metric": opponent["elo_rating"],
                        "is_average": False
                    }
                elif len(most_played_result) > 1:
                    total_elo = sum(player["elo_rating"] for player in most_played_result)
                    average_elo = total_elo / len(most_played_result)
                    opp_info_list = []
                    for opponent in most_played_result:
                        opp_info_list.append({
                            "name": opponent["name"],
                            "surname": opponent["surname"],
                        })
                    most_frequent_stats = {
                        "opponents_info": opp_info_list,
                        "elo_rating_metric": round(average_elo, 2),
                        "is_average": True
                    }
            else: # No opponents played or error in db call (though db call returns list)
                most_frequent_stats = None
                if not opponents_list: # Only flash if there's genuinely no data
                     flash("No match history found to calculate co-player statistics.", "info")


        except Exception as e:
            flash(f"Error fetching player stats: {str(e)}", "danger")
        finally:
            conn.close()
            
    return render_template('view_co_player_stats.html', opponents=opponents_list, most_frequent_opponent_stats=most_frequent_stats)


if __name__ == '__main__':
    # It's good practice to ensure the 'templates' directory exists if not already handled
    import os
    if not os.path.exists('CMPE321HW3/templates'): # Adjust path if main.py is not in CMPE321HW3
        print("Warning: 'templates' directory not found at expected location.")
    
    # Check if create_tables.py needs to be run
    # For a real app, you'd have a proper migration system or setup script.
    # print("Ensure database tables are created by running create_tables.py if this is the first setup.")
    
    app.run(debug=True, port=5001) # Using port 5001 to avoid common conflicts
