# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.tools import (
    add_recipe,
    check_pantry_match,
    find_ingredient_substitute,
    generate_recipe_image,
    get_recipe_details,
    list_recipes,
    search_web_recipes,
)

import json
from pathlib import Path
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

MODEL = "gemini-3.8-flash"

# Load the Agent Engine Sandbox created for this project
SANDBOX_RESOURCE_NAME = "projects/74976572606/locations/us-east1/reasoningEngines/5747768502454845440/sandboxEnvironments/6900262297038487552"

sandbox_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
)


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="sous_chef_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are Sous-Chef AI, an expert personal chef and meal planner. "
        "You remember the user's stated dietary restrictions, allergies, taste preferences, family size, "
        "and pantry habits across conversations, and use them to personalize your recommendations. "
        "You help users discover recipes, inspect ingredients, plan meals tailored to dietary "
        "needs, compare pantry ingredients to generate missing shopping lists using check_pantry_match, "
        "find smart ingredient substitutions using find_ingredient_substitute, "
        "generate dish photography and plating previews using generate_recipe_image, "
        "search the global culinary web database using search_web_recipes, "
        "and save new recipe creations to their cookbook catalog using your Firestore tools. "
        "You also have Python code execution enabled via Agent Platform sandbox. When you need to perform "
        "precise culinary math, ingredient ratio calculations, unit conversions, or data transformations, "
        "write and execute Python code in your sandbox. "
        "When asked for recipes outside the user's saved cookbook or to search online/web recipes, use search_web_recipes. "
        "When asked about substitutions or missing ingredients, use find_ingredient_substitute. "
        "When asked for a picture, preview, or image of a dish, use generate_recipe_image. "
        "When asked what someone can make with their ingredients or what they need to buy, use check_pantry_match. "
        "When asked about saved cookbook recipes, use list_recipes to find options or get_recipe_details to see "
        "step-by-step instructions. You can also save new user creations with add_recipe."
    ),
    code_executor=sandbox_executor,
    tools=[
        PreloadMemoryTool(),
        list_recipes,
        get_recipe_details,
        add_recipe,
        check_pantry_match,
        find_ingredient_substitute,
        generate_recipe_image,
        search_web_recipes,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
