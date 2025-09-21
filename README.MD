# Pennapps 2025 - by Tejas, Ishaan, Henry, and Marcus

# OverSEA

Dark vessel scanning for sustainable seas.

# Overview

One-third of fish stocks are operated beyond sustainable levels and an estimated 30–50% of critical marine habitats have been lost due to human industrialization. (Paolo, 2024)

Today, a third of sharks, rays, and chimaeras are at risk of extinction owing to overfishing (Bradley, n.d.), a disaster only made worse by the 72–76% of the world’s non publicly tracked-illegal-industrial fishing vessels.

_Figure 1: 72-76% of industrial fishing vessels are not publicly tracked._
![untracked](untrackedvessels.png)

While coast guards make every effort to apprehend these vessels, dedicating 1 of its 11 statutory missions to protecting marine life, the sheer size of the exclusive economic zones they patrol combined with limited resources makes this a difficult job.

OverSEA uses satellite data combined with the automatic identification system (AIS) broadcasting vessels' positions to detect illegal fishing, and with our ML model and AI agent, streamlines the process of stopping unregistered fishing vessels.

# Key Features

After corroborating the satellite data with AIS data to reveal untracked fishing vessels, each of their points are stored in MongoDB for efficient access and are marked out on a 3D interactive globe for easy, one-click access, and "hot spots" for untracked fishing.

After fetching the satellite data from Global Fishing Watch, each point of fishing vessel detection is stored in MongoDB for efficient access and are marked out on a 3D interactive globe for easy, one-click access.

To interact with the satellite data, users can use the Gemini powered AI agent for actionable suggestions, supported by Exa to research the maritime laws at the coordinates of each fishing vessel. The Gemini report creator estimates the environmental impact of illegal fishing over a user-determined time period, allowing the user to gain a deeper understanding into the global untracked fishing industry. A chat agent is available to help the user process the vessel data for next steps and regions to be prioritized.

While the globe showing general vessel activity is available for all users, Auth0 is used as a secure way to store the clearance level for each user, with certain features only available to higher clearance levels. For example distinction between AIS tracked and non tracked vessels and the AI simulation/research agent are only available to Confidential and above.

# Tech Stack

### Global Fishing Watch
- Satellite Synthetic Aperture Radar (SAR) data from Sentinel-1
- AIS data

### SciPy Clustering Model
- Predicts hot-spots for illegal fishing in the waters
- Density-Based Clustering
- Multi-Factor Risk Assessment
- Hotspot Influence Decay
- Enhanced Risk Models (Port Proximity Factor, Fishing Season Factor)

### Auth0
- Securely controls Clearance Level and specific permissions for each user

### MongoDB
- Stores vessel analysis results-acts as the pipeline between the data and the frontend
- Stores AI agent prompts and responses for context and smooth user experience

### Google Gemini
- Powers AI Agent and creates reports
- Smooths user experience

### Exa
- Researches the local maritime laws of a certain area

# Works Cited

Bradley, S., Cross, A., Maharaj, V., et al. Overfishing. World Wildlife Fund. (n.d.). https://www.worldwildlife.org/threats/overfishing.

Paolo, F.S., Kroodsma, D., Raynor, J. et al. Satellite mapping reveals extensive industrial activity at sea. Nature 625, 85–91 (2024). https://doi.org/10.1038/s41586-023-06825-8
