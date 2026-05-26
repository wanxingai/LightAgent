from openai import OpenAI

client = OpenAI()

def analyze_data(user_input: str, internal_knowledge: str) -> str:
    """
    Analyze the user input combined with internal knowledge using a large model to draw conclusions.
    
    Args:
        user_input (str): The input provided by the user.
        internal_knowledge (str): Internal knowledge to be combined with the user input.
    
    Returns:
        str: The conclusion drawn from the analysis.
    """
    system_prompt = "You are a helpful assistant that analyzes data."
    final_query = f"{user_input}\n{internal_knowledge}"
    
    try:
        response = client.chat.completions.create(
            model="qwen-turbo-2024-11-01",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_query}
            ],
            temperature=0.1,
        )
        conclusion = response.choices[0].message.content
    except Exception as e:
        conclusion = f"Error encountered while analyzing data: {str(e)}"
    
    return conclusion

# 在函数内部定义工具信息
analyze_data.tool_info = {
    "tool_name": "analyze_data",
    "tool_description": "结合用户输入和内部知识，使用大模型进行分析并得出结论",
    "tool_params": [
        {"name": "user_input", "description": "用户提供的输入", "type": "string", "required": True},
        {"name": "internal_knowledge", "description": "内部知识", "type": "string", "required": True}
    ]
}