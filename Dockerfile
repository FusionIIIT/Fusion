# base image  
FROM python:3.8

# setup environment variable for work directory  
ENV FUSION_HOME=/home/app

# make work directory  
RUN mkdir -p $FUSION_HOME

# set work directory  
WORKDIR $FUSION_HOME

# set environment variables  
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy requirements file
COPY requirements.txt $FUSION_HOME

# install dependencies  
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy api directory to docker's work directory. 
COPY . $FUSION_HOME

# Migrate all migrations
# RUN cd FusionIIIT && python manage.py migrate

# port where the Django app runs  
EXPOSE 8010

# start server  
CMD ["python", "manage.py", "runserver", "0.0.0.0:8010"]
