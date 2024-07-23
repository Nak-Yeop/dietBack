# llm.py

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv
import os


load_dotenv()

model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # gpt-4o is set by env
    temperature=1.0,
)


class NutritionInfo(BaseModel):
    food_name: str = Field(description="The name of the food")
    calorie: str = Field(description="The amount of Calories")
    carbohydrate: str = Field(description="The amount of Carbohydrate")
    protein: str = Field(description="The amount of Protein")
    fat: str = Field(description="The amount of Fat")


output_parser = JsonOutputParser(pydantic_object=NutritionInfo)

prompt_template = ChatPromptTemplate.from_template(
    """
    음식이 입력되면 영양정보(이름, 칼로리, 탄수화물, 단백질, 지방)를 분석해줘
    음식 이름을 입력받으면 다음과 같은 조건을 만족하여 추출해줘 
    예를 들어 "돈까스 2개 먹었어"를 입력받으면, (돈까스, 1400,50,90,60) 이런식으로 출력해줘 
    또 다른 예시로 "에너지바 1개 먹었어"를 입력받으면, 출력은 (에너지바, 200,20,12,10) 이런식으로 출력해줘
    
    입력:{string}
    {format_instructions}
    """
).partial(format_instructions=output_parser.get_format_instructions())


def do(param):
    print(f"Received input: {param}")  # Debugging 출력 추가
    prompt_value = prompt_template.invoke({"string": param})
    model_output = model.invoke(prompt_value)
    output = output_parser.invoke(model_output)
    output_dict = output  # 이미 딕셔너리 형태로 반환됨
    output_dict["food_name"] = param  # 음식 이름을 추가
    print(f"Parsed output: {output_dict}")  # Debugging 출력 추가
    return output_dict
