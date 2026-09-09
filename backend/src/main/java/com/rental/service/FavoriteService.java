package com.rental.service;

import com.rental.entity.Apartment;
import com.rental.entity.Favorite;
import com.rental.entity.User;
import com.rental.repository.FavoriteRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;
import java.util.Optional;

@Service
public class FavoriteService {
    @Autowired
    private FavoriteRepository favoriteRepository;

    public List<Favorite> findByTenantId(Long tenantId) {
        return favoriteRepository.findByTenantId(tenantId);
    }

    public boolean isFavorited(Long tenantId, Long apartmentId) {
        return favoriteRepository.existsByTenantIdAndApartmentId(tenantId, apartmentId);
    }

    @Transactional
    public Favorite addFavorite(User tenant, Apartment apartment) {
        if (favoriteRepository.existsByTenantIdAndApartmentId(tenant.getId(), apartment.getId())) {
            throw new RuntimeException("已收藏该房源");
        }
        Favorite favorite = new Favorite();
        favorite.setTenant(tenant);
        favorite.setApartment(apartment);
        return favoriteRepository.save(favorite);
    }

    @Transactional
    public void removeFavorite(Long tenantId, Long apartmentId) {
        favoriteRepository.deleteByTenantIdAndApartmentId(tenantId, apartmentId);
    }

    public long getFavoriteCount(Long apartmentId) {
        return favoriteRepository.countByApartmentId(apartmentId);
    }
}
