#!/bin/bash

# User data script for application instances
# This script installs and configures the application

set -e

# Update system
yum update -y

# Install required packages
yum install -y httpd php php-pgsql postgresql15

# Start and enable Apache
systemctl start httpd
systemctl enable httpd

# Configure Apache
cat > /etc/httpd/conf.d/app.conf << 'EOF'
<VirtualHost *:80>
    DocumentRoot /var/www/html
    ServerName localhost
    
    <Directory /var/www/html>
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog logs/app_error.log
    CustomLog logs/app_access.log combined
</VirtualHost>
EOF

# Create application directory
mkdir -p /var/www/html

# Create simple PHP application
cat > /var/www/html/index.php << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Blast Radius Demo App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Blast Radius Demo Application</h1>
        <p>This is a simple PHP application running on EC2 with RDS backend.</p>
        
        <h2>System Information</h2>
        <ul>
            <li>Instance ID: <?php echo $_SERVER['SERVER_NAME']; ?></li>
            <li>PHP Version: <?php echo phpversion(); ?></li>
            <li>Timestamp: <?php echo date('Y-m-d H:i:s'); ?></li>
        </ul>
        
        <h2>Database Connection Test</h2>
        <?php
        $db_host = '${db_host}';
        $db_name = '${db_name}';
        $db_user = '${db_user}';
        
        try {
            $pdo = new PDO("pgsql:host=$db_host;dbname=$db_name", $db_user);
            echo '<div class="status success">Database connection successful!</div>';
            
            // Create a simple table if it doesn't exist
            $pdo->exec("CREATE TABLE IF NOT EXISTS visits (
                id SERIAL PRIMARY KEY,
                instance_id VARCHAR(255),
                visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )");
            
            // Insert visit record
            $stmt = $pdo->prepare("INSERT INTO visits (instance_id) VALUES (?)");
            $stmt->execute([$_SERVER['SERVER_NAME']]);
            
            // Get visit count
            $stmt = $pdo->query("SELECT COUNT(*) as count FROM visits");
            $count = $stmt->fetch()['count'];
            echo "<p>Total visits recorded: $count</p>";
            
        } catch (PDOException $e) {
            echo '<div class="status error">Database connection failed: ' . $e->getMessage() . '</div>';
        }
        ?>
        
        <h2>Health Check Endpoint</h2>
        <p>This page serves as a health check endpoint for the load balancer.</p>
    </div>
</body>
</html>
EOF

# Create health check endpoint
cat > /var/www/html/health << 'EOF'
OK
EOF

# Set proper permissions
chown -R apache:apache /var/www/html
chmod -R 755 /var/www/html

# Restart Apache
systemctl restart httpd

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/httpd/access_log",
                        "log_group_name": "/aws/ec2/blast-radius-app",
                        "log_stream_name": "{instance_id}/apache-access",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/httpd/error_log",
                        "log_group_name": "/aws/ec2/blast-radius-app",
                        "log_stream_name": "{instance_id}/apache-error",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch agent
systemctl start amazon-cloudwatch-agent
systemctl enable amazon-cloudwatch-agent

echo "Application setup complete!" 