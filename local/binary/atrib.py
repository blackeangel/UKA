import sys
def rul(st):
    result = []
    data = st.replace(' ','')
    for i in data:
        if not i.isdigit():
            data=data.replace(i,'')
    for _ in range(2) :
        if data[0] != '0':
             result.append(data[:4])
             data = data[4:]
        else:
            result.append(data[0])
            data = data[1:]
    result.append(data)
    return ' '.join(result)
 
if __name__ == '__main__':
    print(rul(sys.argv[1]))
