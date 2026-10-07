pipeline {

    agent any

    stages {

        stage('Checkout') {

            steps {

                checkout scm

            }
        }


        stage('Install Dependencies') {

            steps {

                bat 'python -m pip install -r requirements.txt'

            }
        }


        stage('Run Application Check') {

            steps {

                bat 'python -m py_compile app.py'

            }
        }


        stage('Build Docker Image') {

            steps {

                bat 'docker build -t shopzone:latest .'

            }
        }


        stage('Deploy') {

            steps {

                echo 'Deployment stage completed.'

            }
        }

    }


    post {

        success {

            echo 'ShopZone CI/CD Pipeline completed successfully.'

        }

        failure {

            echo 'ShopZone CI/CD Pipeline failed.'

        }

    }
}