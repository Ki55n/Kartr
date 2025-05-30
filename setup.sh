#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting setup of Influencer_kartr repository...${NC}"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Please install git and try again.${NC}"
    exit 1
fi

# Clean existing files except setup script and README
rm -rf Influencer_kartr 2>/dev/null

# Create a directory for the project if it doesn't exist
PROJECT_DIR="Influencer_kartr"
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Creating project directory...${NC}"
    mkdir -p "$PROJECT_DIR"
fi

# Navigate to the project directory
cd "$PROJECT_DIR" || exit

# Clone the repository
echo -e "${YELLOW}Cloning the repository...${NC}"
git clone https://github.com/Shadowmage-commits/Influencer_kartr.git .

# Check if clone was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to clone the repository. Please check the URL and your internet connection.${NC}"
    exit 1
fi

echo -e "${GREEN}Repository cloned successfully!${NC}"

# Check for package.json to determine if it's a Node.js project
if [ -f "package.json" ]; then
    echo -e "${YELLOW}Node.js project detected. Installing dependencies...${NC}"
    
    # Check if npm is installed
    if command -v npm &> /dev/null; then
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies using npm. Trying with yarn...${NC}"
            
            # Try with yarn if npm fails
            if command -v yarn &> /dev/null; then
                yarn install
                if [ $? -ne 0 ]; then
                    echo -e "${RED}Failed to install dependencies using yarn as well.${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}Yarn is not installed. Please install dependencies manually.${NC}"
                exit 1
            fi
        fi
    elif command -v yarn &> /dev/null; then
        yarn install
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies using yarn.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Neither npm nor yarn is installed. Please install a Node.js package manager and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Dependencies installed successfully!${NC}"
# Check for requirements.txt to determine if it's a Python project
elif [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Python project detected. Installing dependencies...${NC}"
    
    # Check if pip is installed
    if command -v pip &> /dev/null; then
        pip install -r requirements.txt
    elif command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    else
        echo -e "${RED}Neither pip nor pip3 is installed. Please install Python package manager and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Dependencies installed successfully!${NC}"
# Check for other common package managers
elif [ -f "composer.json" ]; then
    echo -e "${YELLOW}PHP project detected. Installing dependencies...${NC}"
    if command -v composer &> /dev/null; then
        composer install
    else
        echo -e "${RED}Composer is not installed. Please install Composer and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Dependencies installed successfully!${NC}"
else
    echo -e "${YELLOW}No common package manager configuration found. You may need to install dependencies manually.${NC}"
fi

# Look for setup instructions in common files
echo -e "${YELLOW}Checking for setup instructions...${NC}"
if [ -f "README.md" ]; then
    echo -e "${GREEN}README.md found. Please check it for additional setup instructions.${NC}"
    echo -e "${YELLOW}Quick preview of README.md:${NC}"
    head -n 20 README.md
elif [ -f "INSTALL.md" ]; then
    echo -e "${GREEN}INSTALL.md found. Please check it for additional setup instructions.${NC}"
    echo -e "${YELLOW}Quick preview of INSTALL.md:${NC}"
    head -n 20 INSTALL.md
fi

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}Please refer to the project documentation for information on how to run the application.${NC}"

cd ..
