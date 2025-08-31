(TraeAI-19) C:\Users\Nitro\aicvgen\simplified [0:0] $ python -m streamlit run app.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.100.53:8501
  External URL: http://41.249.76.121:8501

2025-09-01 00:15:23,481 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:15:25,618 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:15:25,620 - __main__ - INFO - User clicked Generate Tailored CV button
2025-09-01 00:15:25,622 - __main__ - INFO - Starting CV generation workflow
2025-09-01 00:15:25,622 - graph - INFO - Starting graph execution with state: input
2025-09-01 00:15:25,734 - nodes - INFO - Starting job description parsing node
2025-09-01 00:15:25,737 - chains - INFO - Creating job description parsing chain
2025-09-01 00:15:25,782 - chains - INFO - Executing job description parsing chain
2025-09-01 00:15:27,456 - chains - INFO - Job Description Parsing completed
2025-09-01 00:15:27,457 - nodes - INFO - Job description parsing successful. Job title: Data Scientist
2025-09-01 00:15:27,459 - nodes - INFO - Starting CV parsing node
2025-09-01 00:15:27,459 - chains - INFO - Creating cv parsing chain
2025-09-01 00:15:27,467 - chains - INFO - Executing cv parsing chain
2025-09-01 00:15:35,649 - chains - INFO - CV parsing completed. Parsed CV for: Anas AKHOMACH
2025-09-01 00:15:35,651 - nodes - INFO - CV parsing successful. Candidate: Anas AKHOMACH
2025-09-01 00:15:35,652 - nodes - INFO - Starting iterative session setup node
2025-09-01 00:15:35,653 - nodes - INFO - Iterative session setup successful
2025-09-01 00:15:35,655 - nodes - INFO - Starting source section mapping node
2025-09-01 00:15:35,656 - chains - INFO - Creating section mapping chain
2025-09-01 00:15:35,665 - chains - INFO - Executing section mapping chain
2025-09-01 00:15:36,493 - chains - INFO - Section Mapping completed
2025-09-01 00:15:36,494 - nodes - INFO - Section mapping successful: executive_summary_source_index=None qualifications_source_index=0
2025-09-01 00:15:36,495 - nodes - INFO - Starting key qualifications generation node
2025-09-01 00:15:36,495 - chains - INFO - Creating key qualifications chain
2025-09-01 00:15:36,502 - chains - INFO - Executing key qualifications chain
2025-09-01 00:15:37,296 - chains - INFO - Key Qualifications completed
2025-09-01 00:15:37,298 - nodes - INFO - Key qualifications generation successful. Added 8 qualifications to tailored_cv
2025-09-01 00:15:37,301 - graph - INFO - Graph execution completed successfully. New step: awaiting_qualifications_review
2025-09-01 00:15:37,302 - __main__ - INFO - Updating application state. Current step: awaiting_qualifications_review
2025-09-01 00:15:37,303 - __main__ - INFO - CV generation step completed successfully
2025-09-01 00:15:37,481 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:15:41,314 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:15:41,328 - __main__ - INFO - User approved qualifications
2025-09-01 00:15:41,329 - graph - INFO - Starting graph execution with state: start_experience_tailoring
2025-09-01 00:15:41,411 - nodes - INFO - Starting iterative experience tailoring node
2025-09-01 00:15:41,413 - chains - INFO - Creating experience tailoring chain
2025-09-01 00:15:41,425 - chains - INFO - Executing experience tailoring chain
2025-09-01 00:15:43,172 - chains - INFO - Experience Tailoring completed
2025-09-01 00:15:43,175 - nodes - INFO - Replacing existing entry at index 0 during revision
2025-09-01 00:15:43,176 - nodes - INFO - Experience entry 1 processed successfully: Data Analyst [Trainee]
2025-09-01 00:15:43,178 - nodes - INFO - Checking if more experience entries need processing
2025-09-01 00:15:43,179 - nodes - INFO - More experience entries to process: 0/3
2025-09-01 00:15:43,181 - graph - INFO - Graph execution completed successfully. New step: awaiting_experience_review
2025-09-01 00:15:43,183 - __main__ - INFO - Updating application state. Current step: awaiting_experience_review
2025-09-01 00:15:43,399 - __main__ - INFO - Workflow controls rendered. Has inputs: True
────────────────────────── Traceback (most recent call last) ───────────────────────────
  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\runtime\scri
  ptrunner\exec_code.py:121 in exec_func_with_error_handling

  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\runtime\scri
  ptrunner\script_runner.py:640 in code_to_exec

  C:\Users\Nitro\aicvgen\simplified\app.py:447 in <module>

    444 │   │   st.json(get_app_state())
    445
    446 if __name__ == "__main__":
  ❱ 447 │   main()
    448

  C:\Users\Nitro\aicvgen\simplified\app.py:435 in main

    432 │
    433 │   st.divider()
    434 │
  ❱ 435 │   render_workflow_controls()
    436 │
    437 │   st.divider()
    438

  C:\Users\Nitro\aicvgen\simplified\app.py:204 in render_workflow_controls

    201 │   # Check if we're in any review state
    202 │   current_step = state.get("current_step", "")
    203 │   if "awaiting" in current_step:
  ❱ 204 │   │   render_section_review_ui(current_step)
    205 │   │   return
    206 │
    207 │   # Always show the generate button, but disable if inputs are missing

  C:\Users\Nitro\aicvgen\simplified\app.py:305 in render_section_review_ui

    302 │   if current_step == "awaiting_qualifications_review":
    303 │   │   render_qualifications_review(state, render_approval_buttons)
    304 │   elif current_step == "awaiting_experience_review":
  ❱ 305 │   │   render_experience_review(state)
    306 │   elif current_step == "awaiting_project_review":
    307 │   │   render_projects_review(state)
    308 │   elif current_step == "awaiting_summary_review":

  C:\Users\Nitro\aicvgen\simplified\ui_components\render_experience.py:104 in
  render_experience_review

    101 │   )
    102 │
    103 │   # Import update_app_state function from app module
  ❱ 104 │   from app import update_app_state
    105 │
    106 │   # Action buttons
    107 │   st.subheader("🎯 Choose Your Action")

  C:\Users\Nitro\aicvgen\simplified\app.py:39 in <module>

     36 logger = logging.getLogger(__name__)
     37
     38 # Page configuration
  ❱  39 st.set_page_config(
     40 │   page_title="AI CV Generator",
     41 │   page_icon="📄",
     42 │   layout="wide",

  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\runtime\metr
  ics_util.py:410 in wrapped_func

  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\commands\pag
  e_config.py:273 in set_page_config

  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\runtime\scri
  ptrunner_utils\script_run_context.py:183 in enqueue
────────────────────────────────────────────────────────────────────────────────────────
StreamlitSetPageConfigMustBeFirstCommandError: `set_page_config()` can only be called
once per app page, and must be called as the first Streamlit command in your script.

For more information refer to the
[docs](https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config)
.
  Stopping...
(TraeAI-19) C:\Users\Nitro\aicvgen\simplified [1:0] $ python -c "import app; print(' No syntax errors found')"
2025-09-01 00:26:04.484 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
 No syntax errors found
(TraeAI-19) C:\Users\Nitro\aicvgen\simplified [0:0] $
(TraeAI-19) C:\Users\Nitro\aicvgen\simplified [0:0] $ python -m streamlit run app.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.100.53:8501
  External URL: http://41.249.76.121:8501

2025-09-01 00:26:24,652 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:04,552 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:06,748 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:06,749 - __main__ - INFO - User clicked Generate Tailored CV button
2025-09-01 00:27:06,750 - __main__ - INFO - Starting CV generation workflow
2025-09-01 00:27:06,750 - graph - INFO - Starting graph execution with state: input
2025-09-01 00:27:06,790 - nodes - INFO - Starting job description parsing node
2025-09-01 00:27:06,791 - chains - INFO - Creating job description parsing chain
2025-09-01 00:27:06,810 - chains - INFO - Executing job description parsing chain
2025-09-01 00:27:08,537 - chains - INFO - Job Description Parsing completed
2025-09-01 00:27:08,540 - nodes - INFO - Job description parsing successful. Job title: Data Scientist
2025-09-01 00:27:08,542 - nodes - INFO - Starting CV parsing node
2025-09-01 00:27:08,542 - chains - INFO - Creating cv parsing chain
2025-09-01 00:27:08,550 - chains - INFO - Executing cv parsing chain
2025-09-01 00:27:16,827 - chains - INFO - CV parsing completed. Parsed CV for: Anas AKHOMACH
2025-09-01 00:27:16,827 - nodes - INFO - CV parsing successful. Candidate: Anas AKHOMACH
2025-09-01 00:27:16,829 - nodes - INFO - Starting iterative session setup node
2025-09-01 00:27:16,829 - nodes - INFO - Iterative session setup successful
2025-09-01 00:27:16,832 - nodes - INFO - Starting source section mapping node
2025-09-01 00:27:16,832 - chains - INFO - Creating section mapping chain
2025-09-01 00:27:16,847 - chains - INFO - Executing section mapping chain
2025-09-01 00:27:17,598 - chains - INFO - Section Mapping completed
2025-09-01 00:27:17,599 - nodes - INFO - Section mapping successful: executive_summary_source_index=None qualifications_source_index=0
2025-09-01 00:27:17,600 - nodes - INFO - Starting key qualifications generation node
2025-09-01 00:27:17,601 - chains - INFO - Creating key qualifications chain
2025-09-01 00:27:17,612 - chains - INFO - Executing key qualifications chain
2025-09-01 00:27:18,498 - chains - INFO - Key Qualifications completed
2025-09-01 00:27:18,499 - nodes - INFO - Key qualifications generation successful. Added 8 qualifications to tailored_cv
2025-09-01 00:27:18,504 - graph - INFO - Graph execution completed successfully. New step: awaiting_qualifications_review
2025-09-01 00:27:18,504 - __main__ - INFO - Updating application state. Current step: awaiting_qualifications_review
2025-09-01 00:27:18,505 - __main__ - INFO - CV generation step completed successfully
2025-09-01 00:27:18,667 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:22,547 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:22,558 - __main__ - INFO - User approved qualifications
2025-09-01 00:27:22,558 - graph - INFO - Starting graph execution with state: start_experience_tailoring
2025-09-01 00:27:22,630 - nodes - INFO - Starting iterative experience tailoring node
2025-09-01 00:27:22,633 - chains - INFO - Creating experience tailoring chain
2025-09-01 00:27:22,646 - chains - INFO - Executing experience tailoring chain
2025-09-01 00:27:24,457 - chains - INFO - Experience Tailoring completed
2025-09-01 00:27:24,459 - nodes - INFO - Replacing existing entry at index 0 during revision
2025-09-01 00:27:24,459 - nodes - INFO - Experience entry 1 processed successfully: Data Analyst [Trainee]
2025-09-01 00:27:24,463 - nodes - INFO - Checking if more experience entries need processing
2025-09-01 00:27:24,463 - nodes - INFO - More experience entries to process: 0/3
2025-09-01 00:27:24,465 - graph - INFO - Graph execution completed successfully. New step: awaiting_experience_review
2025-09-01 00:27:24,466 - __main__ - INFO - Updating application state. Current step: awaiting_experience_review
2025-09-01 00:27:24,656 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:31,757 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:31,778 - ui_components.render_experience - INFO - User approved experience entry 1
2025-09-01 00:27:31,779 - graph - INFO - Starting graph execution with state: continue_experience_tailoring
2025-09-01 00:27:31,842 - nodes - INFO - Starting iterative experience tailoring node
2025-09-01 00:27:31,843 - chains - INFO - Creating experience tailoring chain
2025-09-01 00:27:31,854 - chains - INFO - Executing experience tailoring chain
2025-09-01 00:27:33,543 - chains - INFO - Experience Tailoring completed
2025-09-01 00:27:33,543 - nodes - INFO - Replacing existing entry at index 1 during revision
2025-09-01 00:27:33,544 - nodes - INFO - Experience entry 2 processed successfully: IT Instructor
2025-09-01 00:27:33,546 - nodes - INFO - Checking if more experience entries need processing
2025-09-01 00:27:33,546 - nodes - INFO - More experience entries to process: 1/3
2025-09-01 00:27:33,548 - graph - INFO - Graph execution completed successfully. New step: awaiting_experience_review
2025-09-01 00:27:33,549 - __main__ - INFO - Updating application state. Current step: awaiting_experience_review
2025-09-01 00:27:33,718 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:38,540 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:38,549 - ui_components.render_experience - INFO - User approved experience entry 2
2025-09-01 00:27:38,550 - graph - INFO - Starting graph execution with state: continue_experience_tailoring
2025-09-01 00:27:38,631 - nodes - INFO - Starting iterative experience tailoring node
2025-09-01 00:27:38,632 - chains - INFO - Creating experience tailoring chain
2025-09-01 00:27:38,645 - chains - INFO - Executing experience tailoring chain
2025-09-01 00:27:40,193 - chains - INFO - Experience Tailoring completed
2025-09-01 00:27:40,194 - nodes - INFO - Replacing existing entry at index 2 during revision
2025-09-01 00:27:40,195 - nodes - INFO - Experience entry 3 processed successfully: Mathematics Teacher
2025-09-01 00:27:40,197 - nodes - INFO - Checking if more experience entries need processing
2025-09-01 00:27:40,199 - nodes - INFO - More experience entries to process: 2/3
2025-09-01 00:27:40,202 - graph - INFO - Graph execution completed successfully. New step: awaiting_experience_review
2025-09-01 00:27:40,204 - __main__ - INFO - Updating application state. Current step: awaiting_experience_review
2025-09-01 00:27:40,347 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:48,880 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:48,890 - ui_components.render_experience - INFO - User approved experience entry 3
2025-09-01 00:27:48,890 - graph - INFO - Starting graph execution with state: experience_tailoring_complete
2025-09-01 00:27:48,951 - nodes - INFO - Starting iterative project tailoring node
2025-09-01 00:27:48,952 - chains - INFO - Creating projects tailoring chain
2025-09-01 00:27:48,962 - chains - INFO - Executing projects tailoring chain
2025-09-01 00:27:50,835 - chains - INFO - Projects Tailoring completed
2025-09-01 00:27:50,838 - nodes - INFO - Replacing existing entry at index 0 during revision
2025-09-01 00:27:50,838 - nodes - INFO - Project entry 1 processed successfully: AI-Powered CV Generator - aicvgen (SaaS Project, In Development)
2025-09-01 00:27:50,840 - nodes - INFO - Checking if more project entries need processing
2025-09-01 00:27:50,841 - nodes - INFO - More project entries to process: 0/3
2025-09-01 00:27:50,843 - graph - INFO - Graph execution completed successfully. New step: awaiting_project_review
2025-09-01 00:27:50,848 - __main__ - INFO - Updating application state. Current step: awaiting_project_review
2025-09-01 00:27:51,007 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:57,437 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:27:57,444 - ui_components.render_projects - INFO - User approved project entry 1
2025-09-01 00:27:57,446 - graph - INFO - Starting graph execution with state: continue_projects_tailoring
2025-09-01 00:27:57,510 - nodes - INFO - Starting iterative project tailoring node
2025-09-01 00:27:57,512 - chains - INFO - Creating projects tailoring chain
2025-09-01 00:27:57,523 - chains - INFO - Executing projects tailoring chain
2025-09-01 00:27:59,044 - chains - INFO - Projects Tailoring completed
2025-09-01 00:27:59,045 - nodes - INFO - Replacing existing entry at index 1 during revision
2025-09-01 00:27:59,045 - nodes - INFO - Project entry 2 processed successfully: ERP Process Automation and Dynamic Dashboard Development
2025-09-01 00:27:59,047 - nodes - INFO - Checking if more project entries need processing
2025-09-01 00:27:59,047 - nodes - INFO - More project entries to process: 1/3
2025-09-01 00:27:59,048 - graph - INFO - Graph execution completed successfully. New step: awaiting_project_review
2025-09-01 00:27:59,049 - __main__ - INFO - Updating application state. Current step: awaiting_project_review
2025-09-01 00:27:59,199 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:28:03,006 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:28:03,018 - ui_components.render_projects - INFO - User approved project entry 2
2025-09-01 00:28:03,018 - graph - INFO - Starting graph execution with state: continue_projects_tailoring
2025-09-01 00:28:03,089 - nodes - INFO - Starting iterative project tailoring node
2025-09-01 00:28:03,090 - chains - INFO - Creating projects tailoring chain
2025-09-01 00:28:03,101 - chains - INFO - Executing projects tailoring chain
2025-09-01 00:28:04,778 - chains - INFO - Projects Tailoring completed
2025-09-01 00:28:04,782 - nodes - INFO - Replacing existing entry at index 2 during revision
2025-09-01 00:28:04,782 - nodes - INFO - Project entry 3 processed successfully: Operating Room Scheduling and Management System Optimization (Final Year Project)
2025-09-01 00:28:04,785 - nodes - INFO - Checking if more project entries need processing
2025-09-01 00:28:04,785 - nodes - INFO - More project entries to process: 2/3
2025-09-01 00:28:04,789 - graph - INFO - Graph execution completed successfully. New step: awaiting_project_review
2025-09-01 00:28:04,789 - __main__ - INFO - Updating application state. Current step: awaiting_project_review
2025-09-01 00:28:04,979 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:28:09,643 - __main__ - INFO - Workflow controls rendered. Has inputs: True
2025-09-01 00:28:09,654 - ui_components.render_projects - INFO - User approved project entry 3
2025-09-01 00:28:09,657 - graph - INFO - Starting graph execution with state: projects_tailoring_complete
2025-09-01 00:28:09,723 - nodes - INFO - Starting executive summary generation node
2025-09-01 00:28:09,724 - chains - INFO - Creating executive summary chain
2025-09-01 00:28:09,734 - chains - INFO - Executing executive summary chain
2025-09-01 00:28:11,214 - chains - INFO - Executive Summary completed
2025-09-01 00:28:11,215 - nodes - INFO - Executive summary generation successful. Summary length: 665 characters. Added to tailored_cv.
2025-09-01 00:28:11,217 - graph - INFO - Graph execution completed successfully. New step: awaiting_summary_review
2025-09-01 00:28:11,218 - __main__ - INFO - Updating application state. Current step: awaiting_summary_review
2025-09-01 00:28:11,370 - __main__ - INFO - Workflow controls rendered. Has inputs: True
────────────────────────── Traceback (most recent call last) ───────────────────────────
  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\runtime\scri
  ptrunner\exec_code.py:121 in exec_func_with_error_handling

  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\streamlit\runtime\scri
  ptrunner\script_runner.py:640 in code_to_exec

  C:\Users\Nitro\aicvgen\simplified\app.py:447 in <module>

    444 │   │   st.json(get_app_state())
    445
    446 if __name__ == "__main__":
  ❱ 447 │   main()
    448

  C:\Users\Nitro\aicvgen\simplified\app.py:435 in main

    432 │
    433 │   st.divider()
    434 │
  ❱ 435 │   render_workflow_controls()
    436 │
    437 │   st.divider()
    438

  C:\Users\Nitro\aicvgen\simplified\app.py:204 in render_workflow_controls

    201 │   # Check if we're in any review state
    202 │   current_step = state.get("current_step", "")
    203 │   if "awaiting" in current_step:
  ❱ 204 │   │   render_section_review_ui(current_step)
    205 │   │   return
    206 │
    207 │   # Always show the generate button, but disable if inputs are missing

  C:\Users\Nitro\aicvgen\simplified\app.py:309 in render_section_review_ui

    306 │   elif current_step == "awaiting_project_review":
    307 │   │   render_projects_review(state, update_app_state)
    308 │   elif current_step == "awaiting_summary_review":
  ❱ 309 │   │   render_summary_review(state, render_approval_buttons)
    310 │   else:
    311 │   │   st.error(f"Unknown review state: {current_step}")
    312

  C:\Users\Nitro\aicvgen\simplified\ui_components\render_summary.py:49 in
  render_summary_review

    46 │   │   section_map = state.get("section_map")
    47 │   │   original_summary_section = None
    48 │   │
  ❱ 49 │   │   if source_data and section_map and section_map.executive_summary_index
    50 │   │   │   try:
    51 │   │   │   │   summary_index = section_map.executive_summary_index
    52 │   │   │   │   original_summary_section = source_data.sections[summary_index]

  C:\Users\Nitro\AppData\Roaming\Python\Python313\site-packages\pydantic\main.py:994
  in __getattr__

     991 │   │   │   │   │   │   return super().__getattribute__(item)  # Raises Attri
     992 │   │   │   │   │   else:
     993 │   │   │   │   │   │   # this is the current error
  ❱  994 │   │   │   │   │   │   raise AttributeError(f'{type(self).__name__!r} object
     995 │   │
     996 │   │   def __setattr__(self, name: str, value: Any) -> None:
     997 │   │   │   if (setattr_handler := self.__pydantic_setattr_handlers__.get(nam
────────────────────────────────────────────────────────────────────────────────────────
AttributeError: 'SectionMap' object has no attribute 'executive_summary_index'