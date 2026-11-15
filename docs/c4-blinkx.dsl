workspace "BlinkX" "C4 (context + containers) simplificado para el pitch — NASA Space Apps 2026" {

    model {
        investigador = person "Investigador/a" "Estudiante o profesional que explora el cielo sin ser especialista" "Person"
        nasa = softwareSystem "SPHEREx (NASA / IRSA)" "Archivo: bucket S3 + SIA2/IRSA" "External System"

        blinkx = softwareSystem "BlinkX" "Convierte imagenes infrarrojas de SPHEREx en videos por coordenadas" {
            frontend = container "Frontend (React)" "Formulario RA/Dec + reproductor de epocas" "React + Vite + Tailwind" 
            backend = container "Backend /frames" "Busca, recorta, alinea y renderiza" "Python + FastAPI" 
            cloudfront = container "CloudFront + S3" "Distribuye el sitio construido" "AWS" "Database"
        }

        investigador -> frontend "Escribe coordenadas y pulsa play" "HTTPS"
        frontend -> backend "Pide /frames?ra&dec&size&band" "HTTPS"
        backend -> nasa "Descarga FITS y recortes" "S3 anónimo"
        frontend -> cloudfront "Servido por" "HTTPS"
    }

    views {
        systemContext blinkx "SystemContext" {
            include *
            autoLayout
        }
        container blinkx "Containers" {
            include *
            autoLayout
        }
        styles {
            element "Person" {
                shape person
            }
            element "External System" {
                background #999999
            }
            element "Database" {
                shape cylinder
            }
        }
    }
}
