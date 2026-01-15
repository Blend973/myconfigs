import sys

while True:
    while True:
        print('Enter the Nth Fibonacci number you wish to')
        print('calculate (such as 5, 50, 1000) or QUIT to quit:')
        response = input('> ')
        
        if response == 'quit':
            print('Thanks for playing!')
            sys.exit()
        if response.isdecimal() and int(response) != 0:
            nth = int(response)
            break
        print('Please enter a number greater than 0.')
    print()

    if nth == 1:
        print('0')
        print()
        print('The #1 Fibonacci number is 0.')
        continue
    elif nth == 2:
        print('o, 1')
        print()
        print('The #2 Fibonacci number is 1.')
        continue
    if nth >= 10000:
        print("This will take a while to display on the screen.")
        input('press Enter to begin.......')

    secondTolastNumber = 0
    lastNumber = 1
    fibNumbeCalculated = 2
    print('o, 1, ', end='')

    while True:
        nextNumber = secondTolastNumber + lastNumber
        fibNumbeCalculated += 1
        print(nextNumber, end='')

        if fibNumbeCalculated == nth:
            print()
            print()
            print('The #', fibNumbeCalculated, 'Fibonacci', 'number is ', nextNumber, sep='')
            break
        print(', ', end='')

        secondTolastNumber = lastNumber
        lastNumber = nextNumber
