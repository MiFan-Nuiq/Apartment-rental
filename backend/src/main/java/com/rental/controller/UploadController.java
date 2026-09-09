package com.rental.controller;

import com.rental.dto.ApiResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

@RestController
@RequestMapping("/api/upload")
public class UploadController {

    @Value("${upload.path:uploads}")
    private String uploadPath;

    @PostMapping
    public ApiResponse<String> upload(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ApiResponse.error("请选择文件");
        }

        try {
            String originalFilename = file.getOriginalFilename();
            String extension = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                extension = originalFilename.substring(originalFilename.lastIndexOf("."));
            }

            String datePath = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
            String newFilename = UUID.randomUUID().toString() + extension;

            File uploadDir = new File(uploadPath);
            if (!uploadDir.isAbsolute()) {
                String userDir = System.getProperty("user.dir");
                uploadDir = new File(userDir, uploadPath);
            }

            File fullPathDir = new File(uploadDir, datePath);
            if (!fullPathDir.exists()) {
                boolean created = fullPathDir.mkdirs();
                if (!created) {
                    return ApiResponse.error("无法创建上传目录");
                }
            }

            File destFile = new File(fullPathDir, newFilename);
            file.transferTo(destFile.getAbsoluteFile());

            String fileUrl = "/uploads/" + datePath + "/" + newFilename;
            return ApiResponse.success("上传成功", fileUrl);
        } catch (IOException e) {
            e.printStackTrace();
            return ApiResponse.error("上传失败: " + e.getMessage());
        }
    }
}
