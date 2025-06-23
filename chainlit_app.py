import chainlit as cl
from dotenv import load_dotenv
import uuid
import asyncio
from src.graphs.agent_flow_v2 import AgentFlowV2

# Load environment variables
load_dotenv()

@cl.on_chat_start
async def on_chat_start():
    """Initialize the agent workflow when a new chat session starts"""
    # Create the agent workflow
    app = AgentFlowV2()()
    
    # Create a unique thread ID for this session
    thread_id = str(uuid.uuid4())
    
    # Store the app and thread config in the user session
    cl.user_session.set("app", app)
    cl.user_session.set("config", {"configurable": {"thread_id": thread_id}})
    
    # Send welcome message
    await cl.Message(
        content="🤖 **Agent Workflow Ready!** \n\nI'm powered by a multi-agent system that can help with research, coding, validation, and more. What would you like me to help you with?",
        author="Assistant"
    ).send()

@cl.step
async def process_node_step(node_name: str, content: str):
    """Process a single node in the workflow"""
    await cl.sleep(0.1)
    return f"Processed by {node_name}: {content}"               

@cl.on_message
async def on_message(message: cl.Message):
    """Handle incoming messages and process them through the agent workflow"""
    
    # Get the app and config from user session
    app = cl.user_session.get("app")
    config = cl.user_session.get("config")
    
    if not app or not config:
        await cl.Message(
            content="❌ Session not initialized properly. Please refresh the page.",
            author="System"
        ).send()
        return
    
    # Prepare the input for the workflow
    inputs = {
        "messages": [
            ("user", message.content),
        ]
    }
    
    # Create a message to stream the response
    response_msg = cl.Message(content="", author="Assistant")
    
    try:
        # Process the message through the workflow
        final_content = ""
        node_outputs = []
        
        # Stream events from the workflow
        async with cl.Step(name="Agent Workflow", type="run") as main_step:
            # main_step.input = message.content
            async for event in app.astream(inputs, config=config):
                for key, value in event.items():
                    if value is None:
                        continue
                        
                    # Get the last message from the event
                    messages = value.get("messages", [])
                    tool_calls_made = value.get("tool_calls_made", [])
                    if messages:
                        last_message = messages[-1]

                        # For intermediate steps, we can show progress
                        if key == "supervisor":
                            async with cl.Step(name="Supervisor", type="tool") as step:
                                step.input = "Analyzing your request and routing it to the appropriate agent"
                                await cl.sleep(0.1)

                                # show supervisor reasonig if available
                                supervisor_reason = value.get("supervisor_reason", [])
                                if supervisor_reason:
                                    step.output = f"Supervisor reasoning: {supervisor_reason[-1]}"
                                else:
                                    step.output = "Request routed successfully"

                        elif key == "enhancer":
                            async with cl.Step(name="Enhancer", type="tool") as step:
                                step.input = "Enhancing and clarifying the request"

                                # Build output with content and tool calls available
                                output_parts = []
                                if hasattr(last_message, "content") and last_message.content:
                                    content = last_message.content[:300] + "..." if len(last_message.content) > 300 else last_message.content
                                    output_parts.append(f"**Enhanced Content:**\n{content}")

                                if tool_calls_made:
                                    output_parts.append(f"**Tools Used:**\n{', '.join(tool_calls_made)}")
                                step.output = "\n".join(output_parts) if output_parts else "Enhancement completed"

                        elif key == "researcher":
                            async with cl.Step(name="Researcher", type="tool") as step:
                                step.input = "Researching the request"

                                # Build output with content and tool calls available
                                output_parts = []
                                if hasattr(last_message, "content") and last_message.content:
                                    content = last_message.content[:300] + "..." if len(last_message.content) > 300 else last_message.content
                                    output_parts.append(f"**Research Content:**\n{content}")

                                if tool_calls_made:
                                    output_parts.append(f"**Tools Used:**\n{', '.join(tool_calls_made)}")
                                step.output = "\n".join(output_parts) if output_parts else "Research completed"

                        elif key == "analyst":
                            async with cl.Step(name="Analyst", type="tool") as step:
                                step.input = "Analyzing the request"

                                # Build output with content and tool calls available
                                output_parts = []
                                if hasattr(last_message, "content") and last_message.content:
                                    content = last_message.content[:300] + "..." if len(last_message.content) > 300 else last_message.content
                                    output_parts.append(f"**Analyst Content:**\n{content}")

                                if tool_calls_made:
                                    output_parts.append(f"**Tools Used:**\n{', '.join(tool_calls_made)}")
                                step.output = "\n".join(output_parts) if output_parts else "Analysis completed"

                        elif key == "validator":
                            async with cl.Step(name="Validator", type="tool") as step:
                                step.input = "Validating the request"

                                # Build output with content and tool calls available
                                output_parts = []
                                if hasattr(last_message, "content") and last_message.content:
                                    content = last_message.content[:300] + "..." if len(last_message.content) > 300 else last_message.content
                                    output_parts.append(f"**Validator Content:**\n{content}")

                                if tool_calls_made:
                                    output_parts.append(f"**Tools Used:**\n{', '.join(tool_calls_made)}")
                                step.output = "\n".join(output_parts) if output_parts else "Validation completed"

                        if (hasattr(last_message, 'name') and 
                            last_message.name in ["final_output_provider", "general_answer_provider"]):
                            final_content = last_message.content

            # main_step.output = final_content
        
        # Send the final response
        if final_content:
            response_msg.content = final_content
            await response_msg.send()
        else:
            await cl.Message(
                content="⚠️ No final output received from the workflow. Please try again.",
                author="System"
            ).send()
            
    except Exception as e:
        await cl.Message(
            content=f"❌ **Error**: {str(e)}\n\nPlease try again or contact support if the issue persists.",
            author="System"
        ).send()

if __name__ == "__main__":
    # This won't be called when using chainlit run, but useful for reference
    print("To run this app, use: chainlit run chainlit_app.py -w") 