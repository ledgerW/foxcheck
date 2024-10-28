import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.documents.base import Document
from langchain_qdrant import QdrantVectorStore
from langchain_community.vectorstores import Qdrant
from langchain_core.vectorstores import VectorStoreRetriever
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from typing import Literal, Optional, List, Any
from uuid import UUID


class QdrantVectorstoreHelper:
    def __init__(self) -> Any:
        self.client = None

        if os.getenv('QDRANT_API_KEY') and os.getenv('QDRANT_URL'):        
            self.client = QdrantClient(
                url=os.getenv('QDRANT_URL'),
                api_key=os.getenv('QDRANT_API_KEY')
            )
        else:
            print("Qdrant API Key and URL not present.")


    def create_collection(self, name: str, vector_size: int) -> None:
        if self.client:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
        else:
            print('No Qdrant Client')

    
    def create_local_vectorstore(
            self,
            chunks: List[Document],
            embedding_model: OpenAIEmbeddings | HuggingFaceInferenceAPIEmbeddings = OpenAIEmbeddings(model='text-embedding-3-large'),
            vector_size: int = 3072
        ) -> None:
        self.local_vectorstore = Qdrant.from_documents(
            documents=chunks,
            vector_params={'size': vector_size, 'distance': Distance.COSINE},
            embedding=embedding_model,
            batch_size=32 if type(embedding_model) == HuggingFaceInferenceAPIEmbeddings else 64,
            location=":memory:"
        )

    
    def create_cloud_vectorstore(
            self,
            chunks: List[Document],
            collection_name: str,
            embedding_model: OpenAIEmbeddings | HuggingFaceInferenceAPIEmbeddings = OpenAIEmbeddings(model='text-embedding-3-large'),
            vector_size: int = 3072
        ) -> None:
        try:
            self.cloud_vectorstore = QdrantVectorStore.from_existing_collection(
                embedding=embedding_model,
                collection_name=collection_name,
                url=os.getenv('QDRANT_URL'),
                api_key=os.getenv('QDRANT_API_KEY')
            )
        except:
            self.cloud_vectorstore = QdrantVectorStore.from_documents(
                documents=chunks,
                embedding=embedding_model,
                vector_params={'size': vector_size, 'distance': Distance.COSINE},
                collection_name=collection_name,
                batch_size=4 if type(embedding_model) == HuggingFaceInferenceAPIEmbeddings else 64,
                prefer_grpc=True,
                url=os.getenv('QDRANT_URL'),
                api_key=os.getenv('QDRANT_API_KEY')
            )


    def add_docs_to_vectorstore(
            self, 
            collection_name: Literal['memory'] | str,
            chunks: List[Document],
            uuids: UUID
        ) -> None:
        str_uuids = [str(uuid) for uuid in uuids]
        if collection_name == 'memory':
            self.local_vectorstore.add_documents(documents=chunks, ids=str_uuids)
        else:
            self.cloud_vectorstore = QdrantVectorStore.from_existing_collection(
                collection_name=collection_name,
                url=os.getenv('QDRANT_URL'),
                api_key=os.getenv('QDRANT_API_KEY')
            )

            self.cloud_vectorstore.add_documents(documents=chunks, ids=str_uuids)


    def get_retriever(
            self, 
            collection_name: Literal['memory'] | str,
            k: int = 3,
            embedding_model: OpenAIEmbeddings = OpenAIEmbeddings(model='text-embedding-3-large')
        ) -> VectorStoreRetriever:
        if collection_name == 'memory':
            return self.local_vectorstore.as_retriever(search_kwargs={'k': k})
        else:
            self.cloud_vectorstore = QdrantVectorStore.from_existing_collection(
                collection_name=collection_name,
                embedding=embedding_model,
                url=os.getenv('QDRANT_URL'),
                api_key=os.getenv('QDRANT_API_KEY')
            )

            return self.cloud_vectorstore.as_retriever(search_kwargs={'k': k})