import json, sys, asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest
import streamlit as st
import plotly.graph_objects as go
from google import genai

with open('secrets.json') as rf:
	values = json.load(rf)
	api_id = values['API_ID']
	api_hash = values['API_HASH']
	gemini_api_key = values['GEMINI_API_KEY']

if len(sys.argv) > 1:
	limit = int(sys.argv[1])
else:
	limit = 100

async def fetch_messages():
	async with TelegramClient('telethon', api_id=api_id, api_hash=api_hash) as client:
		await client.start()

		group = await client.get_entity('cubanjobs')

		history = await client(
			GetHistoryRequest(
				peer=group, limit=limit, offset_date=None, offset_id=0,
				max_id=0, min_id=0, add_offset=0, hash=0
			)
		)

		return history.messages

result = asyncio.run(fetch_messages())

SKILLS = {
	'angular': 'Angular',
	'aspnet': 'ASP.NET',
	'c#': 'C#',
	'django': 'Django',
	'flutter': 'Flutter',
	'javascript': 'JavaScript',
	'laravel': 'Laravel',
	'nodejs': 'Node.js',
	'php': 'PHP',
	'python': 'Python',
	'react': 'React',
	'typescript': 'TypeScript',
	'vuejs': 'Vue.js'
}

messages = []

for message in result:
	if not message.message is None and message.message.strip():
		message = message.message

		message = ''.join(
			c for c in message.lower() if c.isalpha() or c.isspace() or c in '/+#' # (+) not split, for C++
		).replace('/', ' ').split()

		for skill in list(SKILLS.keys()):
			if skill in message:
				if not message in messages:
					messages.append(message)
					break

data = {}

for skill in list(SKILLS.keys()):
	data[skill] = [0] * len(messages)

for i in range(len(messages)):
	for word in messages[i]:
		if word in list(SKILLS.keys()):
			data[word][i] = 1

for k in list(data.keys()):
	if sum(data[k]) == 0:
		del data[k]

data = {SKILLS[k]:	v for k, v in data.items()}

st.set_page_config(
	layout='wide',
	page_icon='📈',
	page_title='cubanjobs Trending'
)

st.title('[cubanjobs](https://t.me/cubanjobs) Trending')

skills_demand = {k:	sum(v) for k, v in data.items()}

max_index = list(skills_demand.values()).index(max(list(skills_demand.values())))

pie_chart = go.Figure(
	data=[
		go.Pie(
			hole=0.4,
			labels=list(skills_demand.keys()),
			pull=[0.1 if i == max_index else 0 for i in range(len(skills_demand))],
			textinfo='percent+label',
			textposition='outside',
			values=list(skills_demand.values())
		)
	]
)

pie_chart.update_layout(title='Tech Skills Demand')

def fetch_recommendation():
	client = genai.Client(
		api_key=gemini_api_key
	)

	prompt = (
		f'Given the following JSON representing the demand for different '
		f'software developer skills, identify the best technology to recommend learning. '
		f'Consider not only demand, but also the underlying capabilities, ecosystem, and future potential of each technology. '
		f'Please use HTML tags like <strong> for emphasis instead of Markdown syntax (e.g., **text** becomes <strong>text</strong>). '
		f'Do not mention the JSON directly. Keep the response concise and insightful: {skills_demand}'
	)

	response = client.models.generate_content(
		model='gemini-2.0-flash',
		contents=prompt
	)

	return response.text

ai_recommendation = fetch_recommendation()

with st.expander('Market Data'):
	col1, col2 = st.columns(2, gap='large')

	with col1:
		st.subheader('Data Table')
		st.dataframe(
			[
				{'Skill':	k, 'Demand':	v}
				for k, v in skills_demand.items()
			],
			use_container_width=True
		)

	with col2:
		st.subheader('Pie Chart')
		st.plotly_chart(pie_chart, use_container_width=True)

	st.markdown('### Gemini AI Recommendation')
	st.markdown(f'''
			<div style="
				background-color: #1a1c24;
				border-radius: 8px;
				padding: 1rem;
				margin-top: 1rem;
				margin-bottom: 1rem;
				font-family: monospace;
			">
				{ai_recommendation}
			</div>
		''',
		unsafe_allow_html=True
	)

line_plot = go.Figure()

for skill, v in data.items():
	line_plot.add_trace(
		go.Scatter(
			fill='tozeroy',
			mode='lines',
			name=skill,
			x=list(range(1, len(v) + 1, 1)),
			y=[i * skills_demand[skill] for i in v]
		)
	)

line_plot.update_layout(
	height=500,
	title='Skill Demand by Message',
	xaxis_title='Message Count',
	yaxis_title='Skill Demand Count'
)

st.subheader('Line Plot')
st.plotly_chart(line_plot, use_container_width=True)