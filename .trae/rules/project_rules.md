
  Here is a strict set of rules and instructions for executing the plan. Treat this as the constitution for this project.

  ---

  The Prime Directive: You Are Not Building a Framework

  This is the most important rule. You are building a single, specific application. Every line of code should directly serve the goal of
  generating a tailored CV. Do not write a function, class, or module for "future use" or because it seems like a "cleaner abstraction." If you
  cannot trace a piece of code directly to a feature on the screen, you should not write it.

  ---

  1. Rules of Structure & Files

   1. The `simplified/` Directory is Sacred: All new application code MUST reside within the src/aicvgen/simplified/ directory.
   2. The Six-File Limit: Your entire application logic must be contained within these six files: app.py, state.py, models.py, chains.py, nodes.py,
      graph.py.
   3. No New Files: Do not create new Python files. If a file grows beyond a few hundred lines, your first instinct should be to simplify the
      functions within it, not to split the file. A new file is a sign of expanding complexity.

  2. Rules of State & Data Flow

   1. One Source of Truth: The AppState TypedDict in state.py is the beginning and the end of all state. It is the single, canonical representation
      of the application's memory.
   2. `app.py` is the Gatekeeper: Only the app.py file is permitted to read from or write to st.session_state. No other module should ever import
      or reference Streamlit.
   3. Nodes are Stateless Functions: A node defined in nodes.py must be a pure function. It takes the AppState as input and returns a Python
      dictionary as output. It must not have side effects.
   4. Data Flow is Unidirectional: Data flows in a strict, predictable cycle: app.py calls the graph, which runs a node, which may call a chain.
      The node returns a dictionary, which is merged into the state by the graph, which returns the new state to app.py. That is the only path.

  3. Rules of Implementation & Code

   1. Functions Over Classes: You are not permitted to create new classes. The only classes in this project will be the Pydantic models in
      models.py and the AppState TypedDict. All logic in nodes.py and chains.py must be implemented as standalone functions.
   2. One Chain, One Task: Each function in chains.py must create one LCEL chain that performs a single, specific generation task (e.g., generate
      qualifications, parse a JD).
   3. Nodes Orchestrate, Chains Create: The job of a node in nodes.py is to orchestrate. It prepares data from the AppState and calls a chain. The
      job of a chain in chains.py is to create new information by calling the LLM.
   4. No Direct Communication: Nodes must never call other nodes. Chains must never call other chains. All communication happens via the AppState.
   5. No Config Files: All configuration (model names, temperature settings, prompt templates) should be hard-coded as constants at the top of the
      relevant files. Do not create .yaml, .ini, or config.py files.

  4. Rules of Naming

  Consistency is mandatory.

   * Files: lowercase_with_underscores.py
   * Pydantic Models: PascalCase (e.g., StructuredCV, SkillRequirement)
   * `AppState` TypedDict: AppState
   * Chain Functions: create_verb_noun_chain() (e.g., create_experience_tailoring_chain)
   * Node Functions: verb_noun_node() (e.g., generate_executive_summary_node)
   * Variables: lowercase_with_underscores

  5. The Human-in-the-Loop (HIL) Pattern

  This is the only acceptable way to implement HIL:

   1. HIL is a UI concern, managed exclusively in app.py.
   2. To request user input, a node's only job is to return a dictionary that sets a flag in the state: return {"human_review_required": True}.
   3. The app.py file must check for this flag. If True, it must render the review UI and must not call the graph.
   4. After gathering input, app.py is responsible for updating the state with the feedback and setting human_review_required back to False.

  ---

  The Final Check: A Litmus Test

  Before writing any new function or block of code, answer these three questions. If the answer to any of them is "No," do not write the code.

   1. Necessity: Is this code absolutely essential to generate a piece of the final, tailored CV right now?
   2. Uniqueness: Is this functionality already handled by an existing function or pattern?
   3. Simplicity: Am I doing this in the most direct and simple way possible, or am I adding an abstraction for a future problem I think I might
      have?

  Stick to this constitution, and you will build a clean, maintainable, and powerful application.
