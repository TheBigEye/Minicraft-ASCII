from math import floor
from random import shuffle

class Generator:
    """ My simple and fast "perlin noise" implementation :D """

    @staticmethod
    def perlin(p: list, x: float, y: float, persistence: float, octaves: int) -> float:
        """
            Generates a Perlin noise height value

            Parameters:
                p (list): The permutation list used for generating noise
                x (float): The x-coordinate in the noise space
                y (float): The y-coordinate in the noise space
                persistence (float): Controls the amplitude of each octave
                octaves (int): The number of octaves to compute

            Returns:
                float: The Perlin noise value at the given coordinates
        """

        total: float = 0
        frequency: float = 2.18  # Initial frequency
        amplitude: float = 1.00  # Initial amplitude
        max_value: float = 0  # Used for normalizing the result

        # Sum the noise contributions for each octave
        for _ in range(octaves):
            total += Generator.noise(p, x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence  # Reduce amplitude for subsequent octaves
            frequency *= 2.1  # Increase frequency for subsequent octaves (lacunarity)

        # Normalize the result to be within the range [-1, 1]
        return total / max_value

    @staticmethod
    def humidity(p: list, x: float, y: float, persistence: float, octaves: int) -> float:
        """
            Generates a Perlin noise height value for the humidity

            Parameters:
                p (list): The permutation list used for generating noise
                x (float): The x-coordinate in the noise space
                y (float): The y-coordinate in the noise space
                persistence (float): Controls the amplitude of each octave
                octaves (int): The number of octaves to compute

            Returns:
                float: The humidity value at the given coordinates
        """

        total: float = 0
        frequency: float = 1.5  # Initial frequency
        amplitude: float = 1.00  # Initial amplitude
        max_value: float = 0  # Used for normalizing the result

        # Sum the noise contributions for each octave
        for _ in range(octaves):
            total += Generator.noise(p, x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence  # Reduce amplitude for subsequent octaves
            frequency *= 2.05 # Increase frequency for subsequent octaves (lacunarity)

        # Normalize the result to be within the range [-1, 1]
        return total / max_value


    @staticmethod
    def temperature(p: list, x: float, y: float, persistence: float, octaves: int) -> float:
        """
            Generates a Perlin noise height value for temeprature

            Parameters:
                p (list): The permutation list used for generating noise
                x (float): The x-coordinate in the noise space
                y (float): The y-coordinate in the noise space
                persistence (float): Controls the amplitude of each octave
                octaves (int): The number of octaves to compute

            Returns:
                float: The temperature value at the given coordinates
        """

        total: float = 0
        frequency: float = 3.2  # Initial frequency
        amplitude: float = 1.00  # Initial amplitude
        max_value: float = 0  # Used for normalizing the result

        # Sum the noise contributions for each octave
        for _ in range(octaves):
            total += Generator.noise(p, x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence  # Reduce amplitude for subsequent octaves
            frequency *= 2.15  # Increase frequency for subsequent octaves (lacunarity)

        # Normalize the result to be within the range [-1, 1]
        return total / max_value


    @staticmethod
    def noise(p: list, x: float, y: float) -> float:
        """
            Generates noise value from permutation

            Parameters:
                p (list): The permutation list used for generating noise
                x (float): The x-coordinate in the noise space
                y (float): The y-coordinate in the noise space

            Returns:
                float: The noise value at the given coordinates
        """

        # Calculate the integer part of the coordinates and apply a bitwise AND with 255
        X: int = floor(x) & 255
        Y: int = floor(y) & 255

        # Calculate the fractional part of the coordinates
        x -= floor(x)
        y -= floor(y)

        # Apply fade function to smooth the interpolation
        u: float = Generator.fade(x)
        v: float = Generator.fade(y)

        # Calculate the hash values for the four corners of the cell
        A: int = p[X] + Y
        B: int = p[X + 1] + Y

        # Perform bilinear interpolation and calculate the gradient contributions
        n: float = Generator.lerp(v,
            Generator.lerp(u,
                Generator.grad(p[A], x, y),
                Generator.grad(p[B], x - 1, y)
            ),
            Generator.lerp(u,
                Generator.grad(p[A + 1], x, y - 1),
                Generator.grad(p[B + 1], x - 1, y - 1)
            )
        )

        return n


    @staticmethod
    def fade(t: float) -> float:
        """
        Applies an interpolation function to smooth the noise curve.

        Parameters:
            t (float): The input value to be smoothed.

        Returns:
            float: The smoothed value.
        """

        return t * t * t * (t * (t * 6 - 15) + 10)


    @staticmethod
    def lerp(t: float, a: float, b: float) -> float:
        """
            Performs linear interpolation between two values

            Parameters:
                t (float): The interpolation factor, usually between 0 and 1
                a (float): The start value
                b (float): The end value

            Returns:
                float: The interpolated value
        """

        return a + t * (b - a)


    @staticmethod
    def grad(h: int, x: float, y: float) -> float:
        """
            Computes the dot product of a randomly selected gradient vector and the distance vector

            Parameters:
                h (int): A hash value used to select a gradient
                x (float): The x-component of the distance vector
                y (float): The y-component of the distance vector

            Returns:
                float: The dot product of the gradient and the distance vector
        """

        h = h & 15  # Take the last 4 bits of the hash
        grad = 1 + (h & 7)  # Calculate the gradient direction

        # If the 4th bit is set, negate the gradient
        if h & 8:
            grad = -grad

        return grad * (x + y)


    @staticmethod
    def permutation() -> list:
        """
            Generates a random permutation list used for creating noise

            Returns:
                list: A permutation list of 512 elements (256 original + 256 duplicate)
        """

        p = list(range(256))
        shuffle(p)  # Randomly shuffle the list
        p += p  # Duplicate the list to avoid overflow in noise calculation
        return p
