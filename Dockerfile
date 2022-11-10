FROM python:3.9
RUN apt-get update && apt-get install python-dev python3-dev -y
RUN pip3 install cython
RUN git clone https://github.com/jataware/NeticaPy3.git
WORKDIR NeticaPy3
RUN ./compile_linux.sh /usr/include/python3.9/
RUN pip3 install -e .
RUN pip3 install pandas==1.5.1
WORKDIR /project