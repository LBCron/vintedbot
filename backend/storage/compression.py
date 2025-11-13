"""
Image Compression
Réduit la taille des images de 50-70% tout en préservant la qualité
"""
from PIL import Image
import io
from loguru import logger


class ImageCompressor:
    """
    Compression intelligente des images

    Features:
    - Resize automatique si trop grande (max 2000x2000)
    - Compression JPEG quality 85 (optimal quality/size)
    - Conversion RGB (RGBA → RGB)
    - Optimize=True pour compression maximale
    - Économie moyenne: 50-70% de la taille
    """

    async def compress(
        self,
        image_data: bytes,
        quality: int = 85,
        max_width: int = 2000,
        max_height: int = 2000,
        format: str = 'JPEG'
    ) -> bytes:
        """
        Compresse image tout en préservant qualité

        Args:
            image_data: Données binaires de l'image
            quality: Qualité JPEG (1-100, recommandé: 85)
            max_width: Largeur maximale (resize si dépassé)
            max_height: Hauteur maximale (resize si dépassé)
            format: Format de sortie (JPEG, WEBP)

        Returns:
            Données binaires de l'image compressée
        """
        try:
            # 1. Load image
            img = Image.open(io.BytesIO(image_data))

            original_size = len(image_data)
            original_dims = f"{img.width}x{img.height}"

            logger.debug(f"📸 Original image: {original_dims}, {original_size} bytes")

            # 2. Resize si nécessaire
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                logger.debug(f"📏 Resized to {img.width}x{img.height}")

            # 3. Convert to RGB if needed (pour JPEG)
            if format == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
                # Créer background blanc pour transparence
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                img = background

                logger.debug(f"🎨 Converted {img.mode} → RGB")

            elif img.mode not in ('RGB', 'L'):  # L = grayscale
                img = img.convert('RGB')

            # 4. Compress
            output = io.BytesIO()

            if format == 'JPEG':
                img.save(
                    output,
                    format='JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True  # Progressive JPEG pour meilleure compression
                )
            elif format == 'WEBP':
                # WebP est 25-35% plus petit que JPEG
                img.save(
                    output,
                    format='WEBP',
                    quality=quality,
                    method=6  # Compression maximale
                )
            else:
                # Fallback
                img.save(output, format=format, optimize=True)

            compressed_data = output.getvalue()
            compressed_size = len(compressed_data)

            # Calculate compression ratio
            compression_ratio = (1 - compressed_size / original_size) * 100

            logger.info(
                f"✅ Compressed: {original_size} → {compressed_size} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )

            return compressed_data

        except Exception as e:
            logger.error(f"❌ Compression failed: {e}")
            # Return original if compression fails
            return image_data

    async def compress_webp(
        self,
        image_data: bytes,
        quality: int = 85,
        max_width: int = 2000,
        max_height: int = 2000
    ) -> bytes:
        """
        Compresse en format WebP (25-35% plus petit que JPEG)

        Args:
            image_data: Données binaires de l'image
            quality: Qualité (1-100)
            max_width: Largeur maximale
            max_height: Hauteur maximale

        Returns:
            Données binaires WebP
        """
        return await self.compress(
            image_data,
            quality=quality,
            max_width=max_width,
            max_height=max_height,
            format='WEBP'
        )

    async def get_image_info(self, image_data: bytes) -> dict:
        """
        Récupère informations sur une image

        Args:
            image_data: Données binaires de l'image

        Returns:
            Dict avec width, height, format, mode, size
        """
        try:
            img = Image.open(io.BytesIO(image_data))

            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': len(image_data)
            }

        except Exception as e:
            logger.error(f"❌ Failed to get image info: {e}")
            return {}

    async def validate_image(self, image_data: bytes) -> tuple[bool, str]:
        """
        Valide qu'un fichier est bien une image

        Args:
            image_data: Données binaires

        Returns:
            (is_valid, error_message)
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()  # Verify integrity

            # Check format
            if img.format not in ['JPEG', 'PNG', 'WEBP', 'GIF']:
                return (False, f"Unsupported format: {img.format}")

            # Check size
            if img.width < 100 or img.height < 100:
                return (False, "Image too small (min 100x100)")

            if img.width > 10000 or img.height > 10000:
                return (False, "Image too large (max 10000x10000)")

            return (True, "")

        except Exception as e:
            return (False, f"Invalid image: {str(e)}")
