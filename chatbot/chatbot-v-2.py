import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from dotenv import load_dotenv
import google.generativeai as palm

load_dotenv()

class WebsiteChatbot:
    def __init__(self, api_key):
        
        """Initialize the chatbot with Google PaLM API key"""
        
        palm.configure(api_key=api_key)
        self.website_content = ""
        self.conversation_history = []
        self.chat = None
        # Available models: 'models/gemini-pro'
        self.model = palm.GenerativeModel('gemini-pro')
        
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
        
        """Prepare the context and prompt for PaLM"""
        
        system_message = (
            "You are a helpful assistant that answers questions about a website's content. "
            "Use only the information provided in the website content to answer questions. "
            "If you cannot find relevant information in the content, say so."
        )
        
        # Truncate website content if too long
        max_content_length = 3000
        truncated_content = self.website_content[:max_content_length]
        if len(self.website_content) > max_content_length:
            truncated_content += "... [Content truncated]"
            
        prompt = f"{system_message}\n\nWebsite content:\n{truncated_content}\n\nUser question: {user_input}"
        
        return prompt
        
    def get_response(self, user_input):
        
        """Get response from PaLM"""
        
        if not self.website_content:
            return "Please fetch website content first using fetch_website_content(url)"
            
        try:
            prompt = self.prepare_prompt(user_input)
            
            # Start a new chat if none exists
            if not self.chat:
                self.chat = self.model.start_chat(history=[])
            
            # Get response
            response = self.chat.send_message(prompt)
            
            # Store the conversation
            self.conversation_history.append({
                "user": user_input,
                "assistant": response.text
            })
            
            return response.text
            
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
    api_key = os.getenv('PALM_API_KEY')
    if not api_key:
        print("Please set the PALM_API_KEY environment variable")
        return
        
    chatbot = WebsiteChatbot(api_key)
    chatbot.start_console_chat()

if __name__ == "__main__":
    main()