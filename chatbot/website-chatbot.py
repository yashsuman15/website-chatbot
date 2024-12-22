import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from urllib.parse import urlparse
import time
from dotenv import load_dotenv

load_dotenv()

class WebsiteChatbot:
    def __init__(self, api_key):
        """Initialize the chatbot with OpenAI API key"""
        self.client = OpenAI(api_key=api_key)
        self.website_content = ""
        self.conversation_history = []
        
    def fetch_website_content(self, url):
        """Fetch and parse website content"""
        try:
            # Validate URL
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
                
            # Fetch content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Basic text cleaning
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            self.website_content = '\n'.join(lines)
            
            return "Website content fetched successfully!"
            
        except requests.RequestException as e:
            return f"Error fetching website: {str(e)}"
        except ValueError as e:
            return f"Error: {str(e)}"
            
    def prepare_prompt(self, user_input):
        """Prepare the prompt for ChatGPT"""
        system_message = (
            "You are a helpful assistant that answers questions about a website's content. "
            "Use only the information provided in the website content to answer questions. "
            "If you cannot find relevant information in the content, say so."
        )
        max_content_length = 3000
        truncated_content = self.website_content[:max_content_length]
        if len(self.website_content) > max_content_length:
            truncated_content += "... [Content truncated]"
            
        messages = [
            {"role" : "system", "content": system_message},
            {"role" : "user", "content": f"Website content:\n{truncated_content}\n\nUser question: {user_input}"}
        ]
        
        # Add conversation history for context
        for message in self.conversation_history[-3:]:  # Keep last 3 exchanges
            messages.append(message)
            
        return messages
        
    def get_response(self, user_input):
        """Get response from ChatGPT"""
        if not self.website_content:
            return "Please fetch website content first using fetch_website_content(url)"
            
        try:
            messages = self.prepare_prompt(user_input)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            bot_response = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": bot_response}
            ])
            
            return bot_response
            
        except Exception as e:
            return f"Error getting response: {str(e)}"
            
    def start_console_chat(self):
        """Start interactive console chat"""
        print("Website Chatbot (type 'exit' to quit)")
        print("First, enter the website URL:")
        
        while True:
            url = input("\nURL: ").strip()
            if url.lower() == 'exit':
                break
                
            result = self.fetch_website_content(url)
            print(result)
            
            if "Error" not in result:
                print("\nWebsite content loaded! You can now ask questions about it.")
                while True:
                    user_input = input("\nYou: ").strip()
                    if user_input.lower() == 'exit':
                        return
                    
                    print("\nBot:", self.get_response(user_input))
                    
def main():
    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable")
        return
        
    chatbot = WebsiteChatbot(api_key)
    chatbot.start_console_chat()

if __name__ == "__main__":
    main()
