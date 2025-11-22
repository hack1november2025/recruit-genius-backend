"""Inspect the save_job_to_database tool structure."""
from app.agents.job_generator.tools import save_job_to_database

print(f"Tool type: {type(save_job_to_database)}")
print(f"Tool name: {save_job_to_database.name}")
print("")
print(f"func: {save_job_to_database.func}")
print(f"coroutine: {save_job_to_database.coroutine}")
print("")
print("Checking _arun method...")
print(f"_arun: {save_job_to_database._arun}")

