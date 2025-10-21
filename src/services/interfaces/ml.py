# This file defines the abstract "contract" for all ML services.
# Any class that implements this interface MUST provide concrete logic
# for all the methods defined below.

import uuid
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IMLService(ABC):
    """
    Abstract interface for all Machine Learning model services required
    by the Synapse worker. This defines the contract that the ML team's
    modules must fulfill for successful integration.
    """

    # --- Ingestion & Modality Conversion ---

    @abstractmethod
    async def extract_text_from_image(self, image_data: str) -> str:
        """
        Performs Optical Character Recognition (OCR) on an image.

        Args:
            image_data (str): A base64 encoded string representing the image file.

        Returns:
            str: The extracted text from the image.
        """
        raise NotImplementedError

    @abstractmethod
    async def transcribe_audio(self, audio_data: str) -> str:
        """
        Performs Speech-to-Text (STT) transcription on an audio file.

        Args:
            audio_data (str): A base64 encoded string representing the audio file.

        Returns:
            str: The transcribed text from the audio.
        """
        raise NotImplementedError

    # --- Input Pre-processing & Compression ---

    @abstractmethod
    async def compress_input_text(self, text: str) -> str:
        """
        Conditionally summarizes or compresses long input text to save tokens
        and focus on the core message.

        Args:
            text (str): The input text from the user, OCR, or STT.

        Returns:
            str: The summarized text if it was long, or the original text if it was short.
        """
        raise NotImplementedError

    # --- Natural Language Understanding ---

    @abstractmethod
    async def determine_intent_and_entities(self, text: str) -> Dict[str, Any]:
        """
        Analyzes text to determine the user's primary goal and extract key topics.

        Args:
            text (str): The user's input query (potentially summarized).

        Returns:
            Dict[str, Any]: A dictionary containing the detected intent and any
                            extracted entities. For example:
                            {'intent': 'retrieve_information', 'entities': ['project deadline']}
        """
        raise NotImplementedError

    # --- Memory & Context Retrieval (RAG) ---

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Converts a string of text into a numerical vector embedding.

        Args:
            text (str): The text to be converted into an embedding.

        Returns:
            List[float]: The vector embedding as a list of floating-point numbers.
        """
        raise NotImplementedError

    # --- Synthesis & Generation ---

    @abstractmethod
    async def synthesize_response_from_context(
        self, original_query: str, context_chunks: List[str]
    ) -> str:
        """
        Uses a Generative LLM to synthesize a final answer based on the user's
        original question and the relevant context retrieved from memory.

        Args:
            original_query (str): The user's original, unmodified question.
            context_chunks (List[str]): A list of relevant text snippets retrieved
                                        from the vector database.

        Returns:
            str: The final, synthesized natural language response.
        """
        raise NotImplementedError