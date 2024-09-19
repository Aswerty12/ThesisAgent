# Installation Guide
## Hardware Requirements 
	Modern GPU with at least 4GB VRAM 
	Modern CPU equivalent to AMD Ryzen 7
## Prerequisites
	Git
	Python 3.11 (preferred via anaconda)
	Ffmpeg installed on system.
	Visual Studio Code (recommended)
## Installation of LLM and Implementing API
1. Either git clone or download text-generation-webui from their official GitHub repository page at https://github.com/oobabooga/text-generation-webui
2. Run the one click installer depending on your operating system and select the GPU that your system uses when asked.
3. Go to http://localhost:7860/ to double check that the installation worked
4. Download the model weights of stablelm-zephyr-3b from the official source at https://huggingface.co/stabilityai/stablelm-zephyr-3b and place it within the ‘models’ folder within text-generation-webui.
5. Go to the model tab and tick on the options of ‘load_in_4bit’ and “use_double_quant" for the model and load zephyr-3b into memory. When loaded look at your GPU usage to see if it has properly loaded in.
6. Test the responses from the chat tab to double check.
7. If all is working, make sure that the API is live by checking that the “OpenAI” extension is ticked open when booting. To ensure this happens every time the API is meant to be live run this command within the cmd_*your OS here* script within text-generation-webui, “python server.py --extensions openai --model stablelm-zephyr-3b” which respectively ensures that the right extension and model is loaded in. 
*Note: replace the statement after “—model” with the LLM you are using if you are not using zephyr-3b.
After this is done you now have the LLM loaded on your system with the API available for the agent to use.
## Installation of the Agent
1. The github repository is located at https://github.com/Aswerty12/ThesisAgent git clone the repository into your directory of choice.
2. Move the yaml files located in the ‘data’ folder to the ‘characters’ folder of text-generation-webui
3. On your command line navigate to the folder where the agent program is installed, then run “pip install -r requirements.txt”. It is highly recommended to use a virtual environment via anaconda.
4. Ensure the API is running and capable of receiving input.
5. Run FinalAgent.py via Visual Studio Code.

After this you will now have the ability to run the agent as the researcher did during the course of developing it.
